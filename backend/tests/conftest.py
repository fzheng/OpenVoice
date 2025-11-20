"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import sys
import tempfile
import shutil
from pathlib import Path
import numpy as np
import soundfile as sf
from unittest.mock import MagicMock

# Mock torch and torchaudio since they require specific CUDA setup
sys.modules['torch'] = MagicMock()
sys.modules['torchaudio'] = MagicMock()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_audio_file(temp_dir):
    """Generate a sample audio file for testing"""
    # Create a 1-second sine wave at 440Hz
    sample_rate = 48000
    duration = 1.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)

    # Add some noise
    noise = 0.05 * np.random.randn(len(t))
    audio = (audio + noise).astype(np.float32)

    # Save as WAV file
    audio_path = temp_dir / "test_audio.wav"
    sf.write(audio_path, audio, sample_rate)

    return audio_path


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.get.return_value = None
    return mock_redis


@pytest.fixture
def mock_celery_app():
    """Mock Celery app for testing"""
    mock_celery = MagicMock()
    mock_celery.control.inspect.return_value.active.return_value = {}
    mock_celery.control.inspect.return_value.reserved.return_value = {}
    return mock_celery
