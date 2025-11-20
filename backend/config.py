import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# File Upload Settings
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "mp3,wav,ogg,m4a,flac,aac,wma").split(","))

# Directories
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
PROCESSED_DIR = BASE_DIR / os.getenv("PROCESSED_DIR", "processed")

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# File Retention
FILE_RETENTION_MINUTES = int(os.getenv("FILE_RETENTION_MINUTES", 10))
FILE_RETENTION_SECONDS = FILE_RETENTION_MINUTES * 60

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
# Celery worker memory control (in MB). If set to 0, Celery's memory limit is disabled.
CELERY_MAX_MEMORY_MB = int(os.getenv("CELERY_MAX_MEMORY_MB", 2048))

# Security
ENABLE_VIRUS_SCAN = os.getenv("ENABLE_VIRUS_SCAN", "False").lower() == "true"
CLAMAV_HOST = os.getenv("CLAMAV_HOST", "localhost")
CLAMAV_PORT = int(os.getenv("CLAMAV_PORT", 3310))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

# Model Configuration
DEEPFILTERNET_MODEL = os.getenv("DEEPFILTERNET_MODEL", "DeepFilterNet3")
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", 48000))

# Audio Enhancement Tuning
# Limit how aggressively noise is attenuated (dB). None/-1 disables the limit (full suppression).
NOISE_ATTENUATION_LIMIT_DB = float(os.getenv("NOISE_ATTENUATION_LIMIT_DB", 12))
# Optional output gain to gently lift voices post-enhancement (dB).
OUTPUT_GAIN_DB = float(os.getenv("OUTPUT_GAIN_DB", 0))
