# 🚀 Test Commands - OpenVoice

Multiple ways to run your tests! Choose what works best for you.

---

## ⚡ Single Command (Recommended)

### Option 1: Using Make
```bash
make test
```
Runs both frontend (22 tests) and backend (16 tests) = **38 tests**

### Option 2: Using npm
```bash
npm test
```
Same as `make test` - runs all tests

### Option 3: Using the root package.json
```bash
npm run test
```
Alternative npm command

---

## 📦 Individual Test Suites

### Frontend Only (22 tests)
```bash
# Using Make
make test-frontend

# Using npm (from root)
npm run test:frontend

# Using npm (from frontend dir)
cd frontend && npm test -- --run
```

### Backend Only (16 tests)
```bash
# Using Make
make test-backend

# Using npm (from root)
npm run test:backend

# Using pytest (from backend dir)
cd backend && pytest tests/test_file_handler.py -v
```

---

## 🔄 Watch Mode (Development)

### Frontend Watch Mode
```bash
# Using Make
make test-watch

# Using npm (from root)
npm run test:watch

# Direct command
cd frontend && npm test
```
Tests auto-rerun when you save files!

---

## 📊 Coverage Reports

### Both Frontend + Backend
```bash
# Using Make
make test-coverage

# Using npm
npm run test:coverage
```

### Frontend Coverage Only
```bash
npm run test:coverage:frontend
```
Opens: `frontend/coverage/index.html`

### Backend Coverage Only
```bash
npm run test:coverage:backend
```
Opens: `backend/htmlcov/index.html`

---

## 🐳 Docker Tests

### Run Tests in Docker
```bash
# Using Make
make test-docker

# Using npm
npm run docker:test

# Using Docker directly
docker-compose exec backend pytest -v
```

---

## 🎯 Specific Test Files

### Frontend - App Component Tests
```bash
cd frontend
npm test -- App.test.jsx --run
```

### Frontend - API Tests
```bash
cd frontend
npm test -- api.test.js --run
```

### Backend - File Handler Tests
```bash
cd backend
pytest tests/test_file_handler.py -v
```

### Backend - Audio Processor Tests
```bash
cd backend
pytest tests/test_audio_processor.py -k "test_slider" -v
```

---

## 🛠️ Setup Commands

### Install All Dependencies
```bash
# Using Make
make install

# Using npm
npm run install:all
```

### Install Frontend Only
```bash
make install-frontend
# OR
npm run install:frontend
```

### Install Backend Only
```bash
make install-backend
# OR
npm run install:backend
```

---

## 📋 Complete Makefile Commands

```bash
make help              # Show all available commands
make test              # Run all tests ⭐
make test-frontend     # Run frontend tests
make test-backend      # Run backend tests
make test-watch        # Run tests in watch mode
make test-coverage     # Run tests with coverage
make install           # Install all dependencies
make build             # Build Docker containers
make start             # Start all services
make stop              # Stop all services
make restart           # Restart services
make logs              # Show all logs
make dev               # Start development servers
make clean             # Clean build artifacts
make status            # Show service status
make health            # Check service health
```

---

## 📋 Complete npm Commands

```bash
npm test                       # Run all tests ⭐
npm run test:frontend          # Run frontend tests
npm run test:backend           # Run backend tests
npm run test:watch             # Watch mode
npm run test:coverage          # Coverage reports
npm run install:all            # Install dependencies
npm run dev                    # Start dev servers
npm run build                  # Build frontend
npm run docker:build           # Build Docker
npm run docker:up              # Start Docker
npm run docker:down            # Stop Docker
npm run docker:logs            # Docker logs
npm run docker:test            # Tests in Docker
```

---

## ✅ Expected Results

When you run `make test` or `npm test`, you should see:

```
==================================
Running All Tests
==================================
Running Frontend Tests (22 tests)...
✓ Test Files  2 passed (2)
✓ Tests      22 passed (22)

Running Backend Tests (16 tests)...
======================== 16 passed ========================

==================================
✅ All Tests Complete!
==================================
```

---

## 🎮 Interactive Test UI

```bash
cd frontend
npm run test:ui
```
Opens a browser with interactive test interface!

---

## 🔥 Quick Reference

| What | Command |
|------|---------|
| **Run All Tests** | `make test` or `npm test` |
| Frontend Only | `make test-frontend` |
| Backend Only | `make test-backend` |
| Watch Mode | `make test-watch` |
| Coverage | `make test-coverage` |
| Install All | `make install` |
| Docker Tests | `make test-docker` |
| Help | `make help` |

---

## 💡 Pro Tips

1. **First Time Setup:**
   ```bash
   make install
   ```

2. **Quick Daily Testing:**
   ```bash
   make test
   ```

3. **Development with Auto-Reload:**
   ```bash
   make test-watch
   ```

4. **Before Committing:**
   ```bash
   make test-coverage
   ```

5. **CI/CD Pipeline:**
   ```bash
   make test
   ```

---

## 🐛 Troubleshooting

### "make: command not found"
**Windows:** Install make via `choco install make` or use `npm test` instead
**Mac:** Install via `brew install make`
**Linux:** Should be pre-installed

### "npm: command not found"
Install Node.js from https://nodejs.org/

### "pytest: command not found"
```bash
pip install pytest
```

### Tests fail with import errors
```bash
make install
```

---

## 📚 Documentation

- [RUN_TESTS.md](RUN_TESTS.md) - Simple test commands
- [TESTING.md](TESTING.md) - Comprehensive guide
- [README.md](README.md) - Project documentation

---

**Recommended:** Use `make test` for the best experience! ⭐
