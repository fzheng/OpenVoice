from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import uuid
import logging
import aiofiles
from typing import Optional
import redis
import json

import config
from utils.file_handler import FileHandler, VirusScanner
from utils.file_cleanup import FileCleanupManager
from celery_worker import celery_app, process_audio_task

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="OpenVoice - Audio Enhancement API",
    description="Remove background noise and enhance human voice in audio files",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize utilities
file_handler = FileHandler(
    max_size_bytes=config.MAX_FILE_SIZE_BYTES,
    allowed_extensions=config.ALLOWED_EXTENSIONS
)

virus_scanner = VirusScanner(
    enabled=config.ENABLE_VIRUS_SCAN,
    clamav_host=config.CLAMAV_HOST,
    clamav_port=config.CLAMAV_PORT
)

cleanup_manager = FileCleanupManager(
    directories=[config.UPLOAD_DIR, config.PROCESSED_DIR],
    retention_seconds=config.FILE_RETENTION_SECONDS
)

# Initialize Redis for queue management
try:
    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=True
    )
    redis_client.ping()
    logger.info("Connected to Redis successfully")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Queue features will be limited.")
    redis_client = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "OpenVoice Audio Enhancement API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    redis_status = "connected"
    celery_status = "unknown"

    # Check Redis
    if redis_client:
        try:
            redis_client.ping()
        except Exception:
            redis_status = "disconnected"
    else:
        redis_status = "not configured"

    # Check Celery workers
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        celery_status = "running" if active_workers else "no workers"
    except Exception as e:
        celery_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "redis": redis_status,
        "celery": celery_status,
        "upload_dir": str(config.UPLOAD_DIR),
        "processed_dir": str(config.PROCESSED_DIR),
        "max_file_size_mb": config.MAX_FILE_SIZE_MB,
        "file_retention_minutes": config.FILE_RETENTION_MINUTES
    }


@app.post("/api/upload")
async def upload_audio(
    file: UploadFile = File(...),
    noise_strength: Optional[float] = Form(None),
):
    """
    Upload an audio file for processing

    Returns:
        task_id: Unique identifier for tracking the processing task
    """
    try:
        # Validate file extension
        is_valid, error = file_handler.validate_file_extension(file.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file size
        is_valid, error = file_handler.validate_file_size(file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        # Generate unique task ID and filename
        task_id = uuid.uuid4().hex
        unique_filename = file_handler.generate_unique_filename(file.filename)
        upload_path = config.UPLOAD_DIR / unique_filename
        # Always write processed output as WAV to ensure compatible encoding
        original_ext = Path(file.filename).suffix.lower() or ".wav"
        processed_filename = f"enhanced_{Path(unique_filename).stem}{original_ext}"
        processed_path = config.PROCESSED_DIR / processed_filename

        # Save uploaded file
        async with aiofiles.open(upload_path, 'wb') as f:
            await f.write(content)

        logger.info(f"File uploaded: {unique_filename} ({file_size} bytes)")

        # Validate MIME type
        is_valid, error = file_handler.validate_mime_type(str(upload_path))
        if not is_valid:
            upload_path.unlink()  # Delete invalid file
            raise HTTPException(status_code=400, detail=error)

        # Scan for viruses
        is_clean, error = virus_scanner.scan_file(str(upload_path))
        if not is_clean:
            upload_path.unlink()  # Delete infected file
            raise HTTPException(status_code=400, detail=f"Security scan failed: {error}")

        # Get queue position
        queue_position = 0
        if redis_client:
            try:
                # Get count of pending tasks
                inspect = celery_app.control.inspect()
                active = inspect.active()
                reserved = inspect.reserved()

                active_count = sum(len(tasks) for tasks in (active or {}).values())
                reserved_count = sum(len(tasks) for tasks in (reserved or {}).values())
                queue_position = active_count + reserved_count

                # Store task metadata in Redis
                task_metadata = {
                    "task_id": task_id,
                    "filename": file.filename,
                    "upload_path": str(upload_path),
                    "processed_path": str(processed_path),
                    "status": "queued",
                    "queue_position": queue_position
                }
                redis_client.setex(
                    f"task:{task_id}",
                    config.FILE_RETENTION_SECONDS,
                    json.dumps(task_metadata)
                )
            except Exception as e:
                logger.warning(f"Failed to get queue position: {e}")

        # Build processing options from UI controls
        proc_options = {}
        if noise_strength is not None:
            # Clamp slider 0-10; map to attenuation limit 6-26 dB (higher = stronger suppression)
            strength = max(0.0, min(10.0, float(noise_strength)))
            proc_options["attenuation_limit_db"] = 6 + strength * 2
            # Gentle voice lift that tapers as suppression increases
            proc_options["output_gain_db"] = max(0.0, round(2.0 - strength * 0.1, 2))

        # Submit processing task to Celery
        task = process_audio_task.apply_async(
            args=[str(upload_path), str(processed_path), task_id, proc_options],
            task_id=task_id
        )

        logger.info(f"Processing task submitted: {task_id}")

        return {
            "task_id": task_id,
            "filename": file.filename,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "queue_position": queue_position,
            "estimated_wait_seconds": queue_position * 30,  # Rough estimate
            "retention_minutes": config.FILE_RETENTION_MINUTES,
            "message": "File uploaded successfully. Processing will begin shortly."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a processing task

    Returns:
        status: pending, processing, completed, or failed
        progress: percentage (0-100)
        queue_position: number of tasks ahead in queue
    """
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)

        # Get metadata from Redis if available
        metadata = {}
        if redis_client:
            try:
                task_data = redis_client.get(f"task:{task_id}")
                if task_data:
                    metadata = json.loads(task_data)
            except Exception as e:
                logger.warning(f"Failed to get task metadata: {e}")

        # Determine status and progress
        state = task_result.state
        progress = 0
        queue_position = metadata.get('queue_position', 0)

        # Safely get task info
        task_info = None
        try:
            task_info = task_result.info
        except Exception as e:
            logger.warning(f"Failed to get task info: {e}")
            task_info = None

        if state == 'PENDING':
            status = 'queued'
            progress = 0
        elif state == 'PROCESSING':
            status = 'processing'
            progress = task_info.get('progress', 50) if isinstance(task_info, dict) else 50
            queue_position = 0
        elif state == 'SUCCESS':
            status = 'completed'
            progress = 100
            queue_position = 0
        elif state == 'FAILURE':
            status = 'failed'
            progress = 0
            queue_position = 0
        else:
            status = state.lower()

        response = {
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "queue_position": queue_position
        }

        # Add additional info for completed tasks
        if state == 'SUCCESS' and isinstance(task_info, dict):
            processed_path = Path(task_info.get('output_path', ''))
            if processed_path.exists():
                time_until_deletion = cleanup_manager.get_time_until_deletion(processed_path)
                response.update({
                    "download_ready": True,
                    "duration_seconds": task_info.get('duration_seconds'),
                    "output_size_mb": task_info.get('output_size_mb'),
                    "time_until_deletion_seconds": time_until_deletion
                })

        # Add error info for failed tasks
        if state == 'FAILURE':
            error_msg = "Task failed"
            if isinstance(task_info, dict):
                error_msg = task_info.get('error', 'Unknown error')
            elif isinstance(task_info, Exception):
                error_msg = str(task_info)
            elif task_info:
                try:
                    error_msg = str(task_info)
                except:
                    error_msg = "Task failed with unknown error"
            response["error"] = error_msg

        return response

    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.get("/api/download/{task_id}")
async def download_processed_audio(task_id: str):
    """
    Download the processed audio file

    Returns:
        The enhanced audio file
    """
    try:
        # Get task result
        task_result = celery_app.AsyncResult(task_id)

        if task_result.state != 'SUCCESS':
            raise HTTPException(
                status_code=400,
                detail=f"File not ready. Current status: {task_result.state}"
            )

        # Get output path from task result
        if not isinstance(task_result.info, dict):
            raise HTTPException(status_code=500, detail="Invalid task result")

        output_path = Path(task_result.info.get('output_path', ''))

        # Check if file exists
        if not output_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Processed file not found. It may have been deleted."
            )

        # Get original filename from metadata
        original_filename = "enhanced_audio.wav"
        if redis_client:
            try:
                task_data = redis_client.get(f"task:{task_id}")
                if task_data:
                    metadata = json.loads(task_data)
                    original = metadata.get('filename', 'audio.wav')
                    original_name = Path(original).stem
                    original_ext = Path(original).suffix or ".wav"
                    original_filename = f"enhanced_{original_name}{original_ext}"
            except Exception as e:
                logger.warning(f"Failed to get original filename: {e}")

        # Return file
        return FileResponse(
            path=output_path,
            media_type='audio/wav',
            filename=original_filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.delete("/api/delete/{task_id}")
async def delete_files(task_id: str):
    """
    Manually delete uploaded and processed files for a task

    Returns:
        success: boolean indicating if files were deleted
    """
    try:
        deleted_files = []

        # Get task metadata
        if redis_client:
            try:
                task_data = redis_client.get(f"task:{task_id}")
                if task_data:
                    metadata = json.loads(task_data)
                    upload_path = Path(metadata.get('upload_path', ''))
                    processed_path = Path(metadata.get('processed_path', ''))

                    # Delete files
                    if upload_path.exists():
                        cleanup_manager.delete_file(upload_path)
                        deleted_files.append(str(upload_path.name))

                    if processed_path.exists():
                        cleanup_manager.delete_file(processed_path)
                        deleted_files.append(str(processed_path.name))

                    # Delete metadata
                    redis_client.delete(f"task:{task_id}")
            except Exception as e:
                logger.error(f"Error deleting files: {e}")

        return {
            "success": True,
            "task_id": task_id,
            "deleted_files": deleted_files,
            "message": "Files deleted successfully" if deleted_files else "No files found to delete"
        }

    except Exception as e:
        logger.error(f"Error deleting files: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@app.get("/api/queue")
async def get_queue_status():
    """
    Get current queue status

    Returns:
        active_tasks: number of tasks being processed
        pending_tasks: number of tasks waiting in queue
    """
    try:
        active_count = 0
        reserved_count = 0

        inspect = celery_app.control.inspect()
        active = inspect.active()
        reserved = inspect.reserved()

        if active:
            active_count = sum(len(tasks) for tasks in active.values())
        if reserved:
            reserved_count = sum(len(tasks) for tasks in reserved.values())

        return {
            "active_tasks": active_count,
            "pending_tasks": reserved_count,
            "total_queue": active_count + reserved_count
        }

    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return {
            "active_tasks": 0,
            "pending_tasks": 0,
            "total_queue": 0,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )
