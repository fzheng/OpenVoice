# Quick Start Guide

Get OpenVoice running in 5 minutes!

## Option 1: Docker (Easiest)

### Prerequisites
- Docker Desktop installed
- 4GB RAM available

### Steps

1. **Clone and start**:
```bash
git clone https://github.com/yourusername/OpenVoice.git
cd OpenVoice
docker-compose up -d
```

2. **Wait for services to start** (30-60 seconds):
```bash
docker-compose logs -f
# Press Ctrl+C when you see "Application startup complete"
```

3. **Open your browser**:
- Go to http://localhost
- Upload an audio file
- Download the enhanced version!

That's it!

### Stopping the application:
```bash
docker-compose down
```

---

## Option 2: Local Development (More Control)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis

### Quick Setup

#### 1. Backend (Terminal 1)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Start Redis (separate terminal):
```bash
redis-server
```

Start API:
```bash
uvicorn main:app --reload
```

#### 2. Worker (Terminal 2)
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
celery -A celery_worker.celery_app worker --loglevel=info
```

#### 3. Beat Scheduler (Terminal 3)
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
celery -A celery_worker.celery_app beat --loglevel=info
```

#### 4. Frontend (Terminal 4)
```bash
cd frontend
npm install
npm run dev
```

#### 5. Open Browser
Go to http://localhost:3000

---

## Testing Your Setup

1. Visit http://localhost (Docker) or http://localhost:3000 (local)
2. Upload a sample audio file
3. Wait for processing
4. Download the enhanced audio

## Troubleshooting

### "Can't connect to backend"
- Check if backend is running: http://localhost:8000/api/health
- Verify Redis is running: `redis-cli ping` should return "PONG"

### "Processing stuck in queue"
- Make sure Celery worker is running
- Check worker logs for errors

### "Out of memory"
- Reduce `CELERY_CONCURRENCY` in .env
- Process smaller files

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize settings in `.env` file
- Check [API documentation](http://localhost:8000/docs) (FastAPI auto-docs)

## Need Help?

- GitHub Issues: https://github.com/yourusername/OpenVoice/issues
- See full documentation in README.md
