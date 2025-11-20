# Quick Test Guide - OpenVoice

## 🚀 Run All Tests (One Command)

### Frontend + Backend:
```bash
# Terminal 1 - Frontend
cd frontend && npm test -- --run

# Terminal 2 - Backend
cd backend && pytest tests/test_file_handler.py tests/test_audio_processor.py -v
```

Expected: ✅ **38 tests passing**

---

## 📝 Frontend Tests (22 tests)

```bash
cd frontend

# Run once
npm test -- --run

# Watch mode (recommended for development)
npm test

# With coverage report
npm run test:coverage

# Interactive UI
npm run test:ui
```

**What's tested:**
- Noise reduction slider (your feature!)
- File upload & validation
- API integration
- Progress tracking

---

## 🔧 Backend Tests (16 tests)

```bash
cd backend

# Run working tests
pytest tests/test_file_handler.py tests/test_audio_processor.py -v

# Specific test file
pytest tests/test_file_handler.py -v

# With coverage
pytest tests/test_file_handler.py --cov=utils --cov-report=term-missing
```

**What's tested:**
- File validation (size, type, MIME)
- Audio processing (load, resample, save)
- Slider math (dB conversion, gain compensation)

---

## 🎯 Test Your Slider Feature

```bash
# Frontend - Slider UI
cd frontend
npm test -- App.test.jsx --grep "slider"

# Backend - Parameter Mapping
cd backend
pytest tests/test_audio_processor.py::TestAudioProcessor::test_slider_to_db_mapping -v
pytest tests/test_audio_processor.py::TestAudioProcessor::test_gain_compensation_logic -v
```

---

## 📊 View Coverage Reports

```bash
# Frontend
cd frontend
npm run test:coverage
# Open: coverage/index.html

# Backend
cd backend
pytest --cov=. --cov-report=html
# Open: htmlcov/index.html
```

---

## ⚡ Quick Checks

### Is everything working?
```bash
# Should show 22 passing
cd frontend && npm test -- --run | grep "Tests"

# Should show 16 passing
cd backend && pytest tests/test_file_handler.py tests/test_audio_processor.py | grep "passed"
```

### Watch for changes:
```bash
# Frontend (auto-rerun on save)
cd frontend && npm test

# Backend (need pytest-watch)
cd backend && pip install pytest-watch && ptw
```

---

## 🐳 Docker Tests (Full Suite)

```bash
# Start services
docker-compose up -d

# Run backend tests in container
docker-compose exec backend bash -c "pip install pytest pytest-cov && pytest -v"

# Run with coverage
docker-compose exec backend bash -c "pytest --cov=. --cov-report=term-missing"
```

---

## 🔍 Troubleshooting

### Frontend tests fail?
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install
npm test -- --run
```

### Backend tests fail?
```bash
# Install missing dependencies
cd backend
pip install -r requirements-test.txt pytest pytest-mock pytest-cov httpx
pytest -v
```

### Can't find pytest?
```bash
pip install pytest
```

### Import errors?
```bash
# Make sure you're in the right directory
cd backend  # for backend tests
cd frontend  # for frontend tests
```

---

## 📋 Test Files

```
frontend/src/
  ├── App.test.jsx       → UI component tests
  └── api.test.js        → API client tests

backend/tests/
  ├── test_file_handler.py      → File validation tests
  └── test_audio_processor.py   → Audio processing tests
```

---

## ✅ Success Indicators

You should see:
- ✅ Frontend: `22 passed` in green
- ✅ Backend: `16 passed` in green
- ✅ No red `FAILED` messages
- ✅ Coverage > 80%

---

## 🆘 Need Help?

1. Check [TESTING.md](TESTING.md) for detailed guide
2. Check [TEST_RESULTS.md](TEST_RESULTS.md) for current status
3. Check [TESTS_FINAL_SUMMARY.md](TESTS_FINAL_SUMMARY.md) for complete overview

---

**Last Updated**: After fixing all test issues
**Status**: ✅ All tests passing (38/38 runnable)
