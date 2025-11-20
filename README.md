# OpenVoice - AI-Powered Audio Enhancement

OpenVoice is a web application that removes background noise and enhances human voice in audio files using state-of-the-art AI technology powered by DeepFilterNet.

## Features

### Core Functionality
- **AI-Powered Audio Enhancement**: Uses DeepFilterNet3 for professional-grade noise removal and voice enhancement
- **Simple Upload Interface**: No authentication required - just upload and enhance
- **Real-time Progress Tracking**: Monitor upload and processing progress with live updates
- **Queue Management**: Handles multiple simultaneous users with position tracking
- **Privacy-First**: Automatic file deletion after 10 minutes, no data persistence

### Security
- File size limits (configurable, default 50MB)
- MIME type validation
- Optional virus/malware scanning with ClamAV
- Secure file handling

### User Experience
- Responsive, modern UI built with React and Tailwind CSS
- Upload progress indicator
- Processing queue position display
- Estimated wait times
- One-click download of enhanced audio
- Manual file deletion option

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Audio Processing**: DeepFilterNet (AI-based noise suppression)
- **Task Queue**: Celery with Redis
- **File Handling**: Python libraries (soundfile, librosa, pydub)
- **Security**: python-magic for MIME validation, optional ClamAV integration

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios

### Infrastructure
- **Message Broker**: Redis
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (for production)

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis
- Docker & Docker Compose (for containerized deployment)

### Method 1: Docker Compose (Recommended)

This is the easiest way to get started:

```bash
# Clone the repository
git clone https://github.com/yourusername/OpenVoice.git
cd OpenVoice

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Method 2: Local Development Setup

#### Backend Setup

1. **Install Python dependencies**:
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

2. **Install system dependencies**:

**Windows**:
- Install FFmpeg from https://ffmpeg.org/download.html
- Add to PATH

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install libsndfile1 libmagic1 ffmpeg
```

**macOS**:
```bash
brew install libsndfile libmagic ffmpeg
```

3. **Install Redis**:

**Windows**:
- Download from https://github.com/microsoftarchive/redis/releases
- Or use WSL

**Linux**:
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**macOS**:
```bash
brew install redis
brew services start redis
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run the backend**:
```bash
# Terminal 1: Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Celery worker
celery -A celery_worker.celery_app worker --loglevel=info --concurrency=2

# Terminal 3: Start Celery beat (for file cleanup)
celery -A celery_worker.celery_app beat --loglevel=info
```

#### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Configure environment** (optional):
```bash
# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env
```

3. **Run the development server**:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

4. **Build for production**:
```bash
npm run build
```

## Configuration

### Environment Variables

Backend configuration (`.env`):

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

# File Upload Settings
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=mp3,wav,ogg,m4a,flac,aac,wma
UPLOAD_DIR=./uploads
PROCESSED_DIR=./processed

# File Retention (in minutes)
FILE_RETENTION_MINUTES=10

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_WORKERS=2
CELERY_CONCURRENCY=2

# Security
ENABLE_VIRUS_SCAN=False
CLAMAV_HOST=localhost
CLAMAV_PORT=3310

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Model Configuration
DEEPFILTERNET_MODEL=DeepFilterNet3
AUDIO_SAMPLE_RATE=48000
```

### Optional: ClamAV Virus Scanning

To enable virus scanning:

1. **Install ClamAV**:

**Linux**:
```bash
sudo apt-get install clamav clamav-daemon
sudo freshclam  # Update virus definitions
sudo systemctl start clamav-daemon
```

**macOS**:
```bash
brew install clamav
freshclam
clamd
```

**Windows**:
Download from https://www.clamav.net/downloads

2. **Enable in configuration**:
```env
ENABLE_VIRUS_SCAN=True
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
```

## API Documentation

### Endpoints

#### Upload Audio File
```http
POST /api/upload
Content-Type: multipart/form-data

Request:
- file: Audio file (max 50MB)

Response:
{
  "task_id": "abc123...",
  "filename": "audio.mp3",
  "file_size_mb": 5.2,
  "queue_position": 2,
  "estimated_wait_seconds": 60,
  "retention_minutes": 10
}
```

#### Get Task Status
```http
GET /api/status/{task_id}

Response:
{
  "task_id": "abc123...",
  "status": "processing",  // queued, processing, completed, failed
  "progress": 75,
  "queue_position": 0,
  "download_ready": false
}
```

#### Download Enhanced Audio
```http
GET /api/download/{task_id}

Response: Audio file (audio/wav)
```

#### Delete Files
```http
DELETE /api/delete/{task_id}

Response:
{
  "success": true,
  "task_id": "abc123...",
  "deleted_files": ["file1.mp3", "file2.wav"]
}
```

#### Get Queue Status
```http
GET /api/queue

Response:
{
  "active_tasks": 2,
  "pending_tasks": 5,
  "total_queue": 7
}
```

#### Health Check
```http
GET /api/health

Response:
{
  "status": "healthy",
  "redis": "connected",
  "celery": "running",
  "max_file_size_mb": 50,
  "file_retention_minutes": 10
}
```

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ HTTP
       ▼
┌─────────────────┐
│  React Frontend │
│   (Vite + UI)   │
└──────┬──────────┘
       │
       │ REST API
       ▼
┌──────────────────┐      ┌─────────────┐
│  FastAPI Backend │◄────►│    Redis    │
│  (Upload/Status) │      │  (Broker)   │
└──────┬───────────┘      └──────┬──────┘
       │                         │
       │ Submit Task             │ Get Task
       ▼                         ▼
┌──────────────────┐      ┌─────────────┐
│  Celery Workers  │◄────►│   Storage   │
│  (DeepFilterNet) │      │  (Files)    │
└──────────────────┘      └─────────────┘
       │
       │ Scheduled
       ▼
┌──────────────────┐
│   Celery Beat    │
│ (File Cleanup)   │
└──────────────────┘
```

## Usage

1. **Upload an Audio File**:
   - Click "Click to upload" or drag and drop an audio file
   - Supported formats: MP3, WAV, OGG, M4A, FLAC, AAC, WMA
   - Maximum size: 50MB (configurable)

2. **Wait for Processing**:
   - See your queue position if other users are being processed
   - Monitor real-time progress updates
   - Processing typically takes 30-60 seconds depending on file length

3. **Download Enhanced Audio**:
   - Click "Download Enhanced Audio" when processing completes
   - File is available for 10 minutes

4. **Privacy**:
   - Files are automatically deleted after 10 minutes
   - You can manually delete files anytime using "Delete Files" button
   - No data is stored permanently

## Performance

- **Processing Speed**: ~1-2x real-time (60-second audio takes 30-60 seconds)
- **Concurrent Users**: Supports multiple users with queue management
- **File Size**: Optimized for files up to 50MB
- **Quality**: 48kHz high-quality output

## Troubleshooting

### Backend won't start

**Issue**: ImportError for DeepFilterNet
```bash
# Solution: Reinstall dependencies
pip install --force-reinstall deepfilternet torch torchaudio
```

**Issue**: Redis connection failed
```bash
# Solution: Make sure Redis is running
redis-cli ping  # Should return PONG

# Start Redis if needed
# Linux: sudo systemctl start redis
# macOS: brew services start redis
# Windows: redis-server
```

### Worker won't start

**Issue**: Celery worker connection error
```bash
# Solution: Check Redis connection and restart worker
celery -A celery_worker.celery_app worker --loglevel=debug
```

### Frontend can't connect to backend

**Issue**: CORS errors
```bash
# Solution: Check CORS_ORIGINS in backend .env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Processing fails

**Issue**: Audio processing errors
```bash
# Check logs
docker-compose logs worker

# Or if running locally
celery -A celery_worker.celery_app worker --loglevel=debug
```

### Large file uploads fail

**Issue**: Nginx timeout or size limit
```bash
# Solution: Update nginx.conf
client_max_body_size 100M;
proxy_read_timeout 300s;
```

## Development

### Running Tests

OpenVoice includes comprehensive unit tests for both backend and frontend components.

#### Backend Tests

The backend uses **pytest** for testing. Tests cover:
- File validation and handling
- Audio processing utilities
- API endpoints
- Noise strength parameter mapping
- Error handling

**Setup:**
```bash
cd backend

# Install test dependencies
pip install -r requirements-test.txt
```

**Run all tests:**
```bash
# Run all tests with verbose output
pytest

# Run with coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_file_handler.py

# Run specific test class
pytest tests/test_api.py::TestUploadEndpoint

# Run specific test function
pytest tests/test_api.py::TestUploadEndpoint::test_upload_valid_audio_file

# Run tests in parallel (faster)
pytest -n auto
```

**Run tests with markers:**
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

**View coverage report:**
```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open the report in your browser
# The report will be in htmlcov/index.html
```

#### Frontend Tests

The frontend uses **Vitest** and **React Testing Library**. Tests cover:
- Component rendering
- User interactions
- File upload validation
- Noise reduction slider functionality
- API integration
- State management

**Setup:**
```bash
cd frontend

# Install test dependencies (included in package.json)
npm install
```

**Run all tests:**
```bash
# Run tests in watch mode (for development)
npm test

# Run tests once (for CI/CD)
npm test -- --run

# Run with coverage
npm run test:coverage

# Run tests with UI (interactive)
npm run test:ui
```

**Run specific tests:**
```bash
# Run specific test file
npm test -- App.test.jsx

# Run tests matching pattern
npm test -- --grep "slider"

# Run in watch mode for specific file
npm test -- App.test.jsx --watch
```

**View coverage report:**
```bash
# Generate coverage report
npm run test:coverage

# Coverage report will be in coverage/index.html
```

#### Docker Tests

Run tests inside Docker containers:

**Backend:**
```bash
# Run tests in backend container
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=. --cov-report=term-missing
```

**Worker (same as backend):**
```bash
docker-compose exec worker1 pytest
```

#### Continuous Integration

For CI/CD pipelines, use these commands:

**Backend:**
```bash
cd backend
pip install -r requirements.txt -r requirements-test.txt
pytest --cov=. --cov-report=xml --cov-report=term-missing
```

**Frontend:**
```bash
cd frontend
npm ci
npm run test:coverage
```

#### Test Structure

**Backend Tests (`backend/tests/`):**
```
tests/
├── __init__.py
├── conftest.py                 # Pytest fixtures and configuration
├── test_file_handler.py        # File validation tests
├── test_audio_processor.py     # Audio processing tests
└── test_api.py                 # API endpoint tests
```

**Frontend Tests (`frontend/src/`):**
```
src/
├── App.test.jsx                # Main component tests
├── api.test.js                 # API client tests
└── setupTests.js               # Test configuration
```

#### Writing New Tests

**Backend Test Example:**
```python
import pytest
from utils.file_handler import FileHandler

def test_validate_file_extension():
    handler = FileHandler(max_size_bytes=50*1024*1024,
                         allowed_extensions={'mp3', 'wav'})

    is_valid, error = handler.validate_file_extension('audio.mp3')
    assert is_valid is True
    assert error is None
```

**Frontend Test Example:**
```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

it('updates noise strength when slider is moved', () => {
  render(<App />);

  const slider = screen.getByRole('slider');
  fireEvent.change(slider, { target: { value: '10' } });

  expect(slider).toHaveValue('10');
});
```

### Code Structure

```
OpenVoice/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── celery_worker.py        # Celery tasks
│   ├── config.py               # Configuration
│   ├── requirements.txt        # Python dependencies
│   └── utils/
│       ├── audio_processor.py  # DeepFilterNet integration
│       ├── file_handler.py     # File validation
│       └── file_cleanup.py     # Automatic cleanup
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main UI component
│   │   ├── api.js             # API client
│   │   └── main.jsx           # Entry point
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml          # Container orchestration
├── Dockerfile.backend          # Backend container
├── Dockerfile.frontend         # Frontend container
├── Dockerfile.worker           # Worker container
└── nginx.conf                  # Nginx configuration
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **DeepFilterNet**: https://github.com/Rikorose/DeepFilterNet
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Celery**: https://docs.celeryq.dev/

## Privacy Policy

OpenVoice is designed with privacy in mind:

- **No User Accounts**: No registration or authentication required
- **No Data Storage**: Files are automatically deleted after 10 minutes
- **No Tracking**: We don't track or analyze user behavior
- **Secure Processing**: All processing happens on secure servers
- **Local Deployment**: You can self-host for complete control

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/yourusername/OpenVoice/issues

---

**Built with ❤️ using DeepFilterNet AI**