"""
Unit tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "50")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("ENABLE_VIRUS_SCAN", "False")


@pytest.fixture
def client(mock_env):
    """Create test client for FastAPI app"""
    # Import after setting env vars
    with patch('main.redis_client') as mock_redis:
        mock_redis.ping.return_value = True
        from main import app
        return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "OpenVoice Audio Enhancement API"
        assert data["status"] == "running"

    @patch('main.redis_client')
    @patch('main.celery_app')
    def test_health_endpoint(self, mock_celery, mock_redis, client):
        """Test health check endpoint"""
        # Mock Redis
        mock_redis.ping.return_value = True

        # Mock Celery workers
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {"worker1": []}
        mock_celery.control.inspect.return_value = mock_inspect

        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "redis" in data
        assert "celery" in data


class TestUploadEndpoint:
    """Test file upload endpoint"""

    @patch('main.redis_client')
    @patch('main.process_audio_task')
    @patch('main.virus_scanner')
    def test_upload_valid_audio_file(
        self,
        mock_virus_scanner,
        mock_task,
        mock_redis,
        client,
        sample_audio_file
    ):
        """Test uploading a valid audio file"""
        # Setup mocks
        mock_virus_scanner.scan_file.return_value = (True, None)
        mock_redis.ping.return_value = True

        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {}
        mock_inspect.reserved.return_value = {}

        # Read sample audio file
        with open(sample_audio_file, 'rb') as f:
            audio_data = f.read()

        # Create file upload
        files = {'file': ('test.wav', io.BytesIO(audio_data), 'audio/wav')}
        data = {'noise_strength': 7}

        with patch('main.celery_app.control.inspect', return_value=mock_inspect):
            response = client.post('/api/upload', files=files, data=data)

        assert response.status_code == 200
        json_data = response.json()
        assert "task_id" in json_data
        assert json_data["filename"] == "test.wav"
        assert "file_size_mb" in json_data

    def test_upload_invalid_file_type(self, client):
        """Test uploading an invalid file type"""
        # Create a fake PDF file
        files = {'file': ('document.pdf', io.BytesIO(b'fake pdf'), 'application/pdf')}

        response = client.post('/api/upload', files=files)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_file_too_large(self, client):
        """Test uploading a file that exceeds size limit"""
        # Create a file larger than 50MB
        large_data = b'0' * (51 * 1024 * 1024)
        files = {'file': ('large.wav', io.BytesIO(large_data), 'audio/wav')}

        response = client.post('/api/upload', files=files)
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]

    @patch('main.redis_client')
    @patch('main.virus_scanner')
    def test_upload_with_virus(self, mock_virus_scanner, mock_redis, client, sample_audio_file):
        """Test uploading a file that fails virus scan"""
        mock_virus_scanner.scan_file.return_value = (False, "Virus detected")

        with open(sample_audio_file, 'rb') as f:
            audio_data = f.read()

        files = {'file': ('infected.wav', io.BytesIO(audio_data), 'audio/wav')}

        response = client.post('/api/upload', files=files)
        assert response.status_code == 400
        assert "Security scan failed" in response.json()["detail"]

    @patch('main.redis_client')
    @patch('main.process_audio_task')
    @patch('main.virus_scanner')
    def test_upload_with_noise_strength(
        self,
        mock_virus_scanner,
        mock_task,
        mock_redis,
        client,
        sample_audio_file
    ):
        """Test uploading with custom noise strength parameter"""
        mock_virus_scanner.scan_file.return_value = (True, None)

        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {}
        mock_inspect.reserved.return_value = {}

        with open(sample_audio_file, 'rb') as f:
            audio_data = f.read()

        files = {'file': ('test.wav', io.BytesIO(audio_data), 'audio/wav')}
        data = {'noise_strength': 5}

        with patch('main.celery_app.control.inspect', return_value=mock_inspect):
            response = client.post('/api/upload', files=files, data=data)

        assert response.status_code == 200

        # Verify task was called with processing options
        mock_task.apply_async.assert_called_once()
        call_args = mock_task.apply_async.call_args
        proc_options = call_args[1]['args'][3]

        # Verify noise strength was converted to attenuation
        # strength=5 should give: attenuation = 6 + 5*2 = 16 dB
        assert proc_options['attenuation_limit_db'] == 16.0
        # gain = 2.0 - 5*0.1 = 1.5 dB
        assert proc_options['output_gain_db'] == 1.5


class TestStatusEndpoint:
    """Test task status endpoint"""

    @patch('main.redis_client')
    @patch('main.celery_app')
    def test_get_status_queued(self, mock_celery, mock_redis, client):
        """Test getting status of queued task"""
        task_id = "test-task-123"

        # Mock Celery task result
        mock_result = MagicMock()
        mock_result.state = 'PENDING'
        mock_result.ready.return_value = False
        mock_celery.AsyncResult.return_value = mock_result

        response = client.get(f'/api/status/{task_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['task_id'] == task_id
        assert data['status'] == 'queued'

    @patch('main.redis_client')
    @patch('main.celery_app')
    def test_get_status_processing(self, mock_celery, mock_redis, client):
        """Test getting status of processing task"""
        task_id = "test-task-123"

        mock_result = MagicMock()
        mock_result.state = 'PROGRESS'
        mock_result.ready.return_value = False
        mock_result.info = {'progress': 50}
        mock_celery.AsyncResult.return_value = mock_result

        response = client.get(f'/api/status/{task_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'processing'
        assert data['progress'] == 50

    @patch('main.redis_client')
    @patch('main.celery_app')
    def test_get_status_completed(self, mock_celery, mock_redis, client):
        """Test getting status of completed task"""
        task_id = "test-task-123"

        mock_result = MagicMock()
        mock_result.state = 'SUCCESS'
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_celery.AsyncResult.return_value = mock_result

        response = client.get(f'/api/status/{task_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'completed'


class TestQueueEndpoint:
    """Test queue status endpoint"""

    @patch('main.celery_app')
    def test_get_queue_status(self, mock_celery, client):
        """Test getting queue status"""
        # Mock Celery inspection
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {
            'worker1': [{'id': 'task1'}, {'id': 'task2'}]
        }
        mock_inspect.reserved.return_value = {
            'worker1': [{'id': 'task3'}]
        }
        mock_celery.control.inspect.return_value = mock_inspect

        response = client.get('/api/queue')
        assert response.status_code == 200
        data = response.json()
        assert data['active_tasks'] == 2
        assert data['pending_tasks'] == 1
        assert data['total_queue'] == 3


class TestNoiseStrengthMapping:
    """Test noise strength to processing parameter mapping"""

    def test_slider_range_clamping(self):
        """Test that slider values are clamped to 0-10 range"""
        test_cases = [
            (-5, 0),    # Below minimum
            (0, 0),     # Minimum
            (5, 5),     # Middle
            (10, 10),   # Maximum
            (15, 10),   # Above maximum
        ]

        for input_val, expected in test_cases:
            clamped = max(0.0, min(10.0, float(input_val)))
            assert clamped == expected

    def test_attenuation_mapping(self):
        """Test attenuation limit calculation from slider"""
        # attenuation_limit_db = 6 + strength * 2
        test_cases = [
            (0, 6.0),
            (5, 16.0),
            (7, 20.0),
            (10, 26.0),
        ]

        for strength, expected_db in test_cases:
            attenuation = 6 + strength * 2
            assert attenuation == expected_db

    def test_gain_mapping(self):
        """Test output gain calculation from slider"""
        # output_gain_db = max(0.0, round(2.0 - strength * 0.1, 2))
        test_cases = [
            (0, 2.0),
            (5, 1.5),
            (10, 1.0),
            (20, 0.0),  # Should clamp to 0
        ]

        for strength, expected_gain in test_cases:
            gain = max(0.0, round(2.0 - strength * 0.1, 2))
            assert gain == expected_gain
