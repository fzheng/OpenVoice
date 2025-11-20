# Testing Guide for OpenVoice

This document provides detailed information about testing the OpenVoice application.

## Table of Contents

- [Overview](#overview)
- [Backend Tests](#backend-tests)
- [Frontend Tests](#frontend-tests)
- [Running Tests](#running-tests)
- [Coverage Reports](#coverage-reports)
- [CI/CD Integration](#cicd-integration)
- [Writing Tests](#writing-tests)

## Overview

OpenVoice uses a comprehensive testing strategy covering both backend and frontend:

- **Backend**: pytest with fixtures for mocking external dependencies
- **Frontend**: Vitest with React Testing Library for component testing
- **Coverage**: HTML and terminal coverage reports for both
- **CI/CD Ready**: Tests can run in isolated environments

### Test Statistics

**Backend Tests:**
- File Handler: 12+ tests
- Audio Processor: 15+ tests
- API Endpoints: 20+ tests
- Total: 47+ test cases

**Frontend Tests:**
- Component Tests: 15+ tests
- API Tests: 8+ tests
- Integration Tests: 10+ tests
- Total: 33+ test cases

## Backend Tests

### Test Files

| File | Purpose | Test Count |
|------|---------|------------|
| `test_file_handler.py` | File validation, MIME type checking | 12 |
| `test_audio_processor.py` | Audio loading, processing, normalization | 15 |
| `test_api.py` | FastAPI endpoints, parameter mapping | 20 |

### Key Test Areas

#### 1. File Validation
```python
# Tests file extension validation
def test_validate_file_extension_valid()
def test_validate_file_extension_invalid()
def test_validate_file_extension_case_insensitive()

# Tests file size validation
def test_validate_file_size_within_limit()
def test_validate_file_size_exceeds_limit()

# Tests MIME type validation
def test_validate_mime_type_valid()
def test_validate_mime_type_invalid()
```

#### 2. Audio Processing
```python
# Tests audio loading and conversion
def test_load_audio()
def test_load_audio_mono_conversion()
def test_load_audio_resampling()

# Tests audio normalization
def test_normalize_audio()
def test_normalize_audio_already_normalized()

# Tests dimension handling for DeepFilterNet
def test_enhance_audio_dimension_handling()
```

#### 3. API Endpoints
```python
# Tests upload endpoint
def test_upload_valid_audio_file()
def test_upload_invalid_file_type()
def test_upload_file_too_large()
def test_upload_with_noise_strength()

# Tests status endpoint
def test_get_status_queued()
def test_get_status_processing()
def test_get_status_completed()
```

#### 4. Noise Strength Mapping
```python
# Tests slider to dB conversion
def test_slider_to_db_mapping()
# slider=0 → 6dB, slider=10 → 26dB

def test_gain_compensation_logic()
# slider=0 → 2.0dB gain, slider=10 → 1.0dB gain
```

### Running Backend Tests

**Basic:**
```bash
cd backend
pytest
```

**With Coverage:**
```bash
pytest --cov=. --cov-report=html
```

**Specific Tests:**
```bash
# Single file
pytest tests/test_file_handler.py

# Single test
pytest tests/test_api.py::test_upload_valid_audio_file -v

# Pattern matching
pytest -k "validation"
```

**Parallel Execution:**
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run in parallel
pytest -n auto
```

## Frontend Tests

### Test Files

| File | Purpose | Test Count |
|------|---------|------------|
| `App.test.jsx` | Main component, UI interactions | 15 |
| `api.test.js` | API client functions | 8 |

### Key Test Areas

#### 1. Component Rendering
```javascript
it('renders the main heading')
it('displays privacy notice')
it('shows file upload area by default')
it('displays noise reduction slider with default value')
```

#### 2. User Interactions
```javascript
it('updates noise strength when slider is moved')
it('shows different strength descriptions for slider values')
it('validates file size')
it('validates file type')
it('accepts valid audio file')
```

#### 3. Upload Flow
```javascript
it('calls uploadAudio with correct parameters')
it('displays queue position when task is queued')
it('shows download button when processing is completed')
```

#### 4. Noise Slider Logic
```javascript
it('calculates correct attenuation for slider values')
it('calculates correct gain compensation for slider values')
it('resets slider to default when upload button is clicked')
```

### Running Frontend Tests

**Basic (Watch Mode):**
```bash
cd frontend
npm test
```

**Single Run (CI/CD):**
```bash
npm test -- --run
```

**With Coverage:**
```bash
npm run test:coverage
```

**Interactive UI:**
```bash
npm run test:ui
# Opens browser at http://localhost:51204/__vitest__/
```

**Specific Tests:**
```bash
# Single file
npm test -- App.test.jsx

# Pattern matching
npm test -- --grep "slider"
```

## Coverage Reports

### Backend Coverage

Generate coverage report:
```bash
cd backend
pytest --cov=. --cov-report=html --cov-report=term-missing
```

View report:
```bash
# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**Expected Coverage:**
- File Handler: > 90%
- Audio Processor: > 80%
- API Endpoints: > 85%
- Overall: > 85%

### Frontend Coverage

Generate coverage report:
```bash
cd frontend
npm run test:coverage
```

View report:
```bash
# Open in browser
open coverage/index.html  # macOS
xdg-open coverage/index.html  # Linux
start coverage/index.html  # Windows
```

**Expected Coverage:**
- Components: > 80%
- API Client: > 90%
- Overall: > 85%

## Docker Tests

### Running Tests in Containers

**Backend/Worker:**
```bash
# Run tests in backend container
docker-compose exec backend pytest

# With coverage
docker-compose exec backend pytest --cov=. --cov-report=term-missing

# Specific test
docker-compose exec backend pytest tests/test_file_handler.py -v
```

**Note:** Frontend tests should be run locally during development, not in Docker.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-test.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

## Writing Tests

### Backend Test Template

```python
"""
Test module for [component name]
"""
import pytest
from [module] import [Component]


class Test[Component]:
    """Test [Component] class"""

    @pytest.fixture
    def component(self):
        """Create [Component] instance"""
        return Component(param1=value1)

    def test_[functionality](self, component):
        """Test [specific functionality]"""
        # Arrange
        input_data = ...

        # Act
        result = component.method(input_data)

        # Assert
        assert result == expected_result
        assert result.property == expected_value
```

### Frontend Test Template

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Component from './Component';

describe('Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render correctly', () => {
    render(<Component />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('should handle user interaction', async () => {
    render(<Component />);

    const button = screen.getByRole('button', { name: /Click Me/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Result')).toBeInTheDocument();
    });
  });
});
```

## Best Practices

### General
1. **Write tests first** (TDD) or alongside implementation
2. **Test behavior, not implementation** - Focus on what, not how
3. **Use descriptive test names** - `test_upload_rejects_large_files` not `test_1`
4. **One assertion per test** (when practical)
5. **Arrange-Act-Assert pattern** for clarity

### Backend
1. **Use fixtures** for common setup
2. **Mock external dependencies** (Redis, Celery, file system)
3. **Test edge cases** (empty files, invalid types, etc.)
4. **Parameterize tests** for multiple similar cases
5. **Test error handling** explicitly

### Frontend
1. **Query by accessibility role** (`getByRole`) when possible
2. **Avoid testing internal state** - test user-visible behavior
3. **Use `waitFor`** for async operations
4. **Mock API calls** to avoid network dependencies
5. **Test user flows** end-to-end

## Troubleshooting

### Backend Tests Fail

**Issue: ModuleNotFoundError**
```bash
# Solution: Install dependencies
pip install -r requirements.txt -r requirements-test.txt
```

**Issue: Redis connection error**
```bash
# Solution: Mock Redis in tests (already done in conftest.py)
# Or start Redis locally for integration tests
redis-server
```

**Issue: Audio file not found**
```bash
# Solution: Tests generate sample files automatically
# Ensure temp directory is writable
```

### Frontend Tests Fail

**Issue: Module not found**
```bash
# Solution: Install dependencies
npm install
```

**Issue: Test timeout**
```bash
# Solution: Increase timeout in vitest.config.js
test: {
  testTimeout: 10000
}
```

**Issue: jsdom errors**
```bash
# Solution: Ensure setupTests.js is loaded
# Check vitest.config.js has: setupFiles: './src/setupTests.js'
```

## Quick Reference

### Commands Cheat Sheet

```bash
# Backend
cd backend
pytest                                    # Run all tests
pytest tests/test_api.py                 # Single file
pytest -k "upload"                       # Pattern match
pytest --cov=. --cov-report=html        # With coverage
pytest -n auto                           # Parallel
pytest -v -s                             # Verbose + output
pytest --lf                              # Last failed only

# Frontend
cd frontend
npm test                                 # Watch mode
npm test -- --run                        # Single run
npm run test:coverage                    # Coverage
npm run test:ui                          # UI mode
npm test -- App.test.jsx                # Single file
npm test -- --grep "slider"             # Pattern match

# Docker
docker-compose exec backend pytest
docker-compose exec worker1 pytest tests/test_audio_processor.py
```

---

**Happy Testing! 🧪**

For questions or issues, please open a GitHub issue.
