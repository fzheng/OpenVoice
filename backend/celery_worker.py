from celery import Celery
import config
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'openvoice',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=5,  # Reduced from 50 to free memory more frequently
    worker_max_memory_per_child=(
        0 if config.CELERY_MAX_MEMORY_MB <= 0 else config.CELERY_MAX_MEMORY_MB * 1024
    ),  # Restart worker if RSS exceeds limit (0 disables the check)
)

# Import audio processor
from utils.audio_processor import AudioProcessor

# Initialize audio processor (will be lazy-loaded)
audio_processor = AudioProcessor(
    target_sample_rate=config.AUDIO_SAMPLE_RATE,
    attenuation_limit_db=(
        None
        if config.NOISE_ATTENUATION_LIMIT_DB < 0
        else config.NOISE_ATTENUATION_LIMIT_DB
    ),
    output_gain_db=config.OUTPUT_GAIN_DB,
)


@celery_app.task(bind=True, name='process_audio')
def process_audio_task(self, input_path: str, output_path: str, task_id: str, options: dict = None):
    """
    Celery task to process audio file

    Args:
        input_path: Path to uploaded audio file
        output_path: Path where processed audio should be saved
        task_id: Unique task identifier
    """
    try:
        logger.info(f"Starting audio processing task {task_id}")

        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'Processing audio...',
                'progress': 10
            }
        )

        options = options or {}
        attenuation_limit_db = options.get("attenuation_limit_db")
        output_gain_db = options.get("output_gain_db")

        # Process the audio file
        result = audio_processor.process_file(
            input_path,
            output_path,
            attenuation_limit_db=attenuation_limit_db,
            output_gain_db=output_gain_db,
        )

        if result['success']:
            logger.info(f"Audio processing completed successfully for task {task_id}")
            # Prefer the actual output path returned by processor (may be wav fallback)
            final_output_path = result.get('output_path', output_path)
            return {
                'status': 'completed',
                'task_id': task_id,
                'output_path': final_output_path,
                'duration_seconds': result.get('duration_seconds'),
                'sample_rate': result.get('sample_rate'),
                'output_size_mb': result.get('output_size_mb'),
                'progress': 100
            }
        else:
            logger.error(f"Audio processing failed for task {task_id}: {result.get('error')}")
            raise Exception(result.get('error', 'Unknown error during processing'))

    except Exception as e:
        logger.error(f"Error in audio processing task {task_id}: {str(e)}")
        # Don't manually update state to FAILURE, just re-raise the exception
        # Celery will handle setting the state and exception info properly
        raise


@celery_app.task(name='cleanup_files')
def cleanup_files_task():
    """Background task to cleanup old files"""
    from utils.file_cleanup import FileCleanupManager

    cleanup_manager = FileCleanupManager(
        directories=[config.UPLOAD_DIR, config.PROCESSED_DIR],
        retention_seconds=config.FILE_RETENTION_SECONDS
    )

    deleted_count = cleanup_manager.cleanup_old_files()
    logger.info(f"Cleanup task completed: {deleted_count} files deleted")
    return deleted_count


# Schedule periodic cleanup task
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'cleanup_files',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    },
}
