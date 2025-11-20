# OpenVoice Integration Tests

This directory contains integration tests for the OpenVoice audio enhancement system.

## Test Files

### `test_audio_processing.py`
Comprehensive integration test for the audio processing pipeline.

**What it tests:**
- Test audio generation (sine wave with noise)
- AudioProcessor initialization with DeepFilterNet
- Audio loading and resampling to target sample rate
- Audio enhancement through the complete pipeline
- Output file creation and format validation
- Tensor shape handling (1D/2D conversions)

**Requirements:**
- All backend dependencies (see `backend/requirements.txt`)
- DeepFilterNet model files (downloaded automatically on first run)

## Running Tests

### Inside Docker Container
```bash
# Run the integration test in a worker container
docker-compose exec worker1 python /tmp/test_audio_processing.py
```

### Quick Test (Inline)
```bash
# Run a quick inline test
docker-compose exec worker1 python << 'EOF'
import numpy as np
import soundfile as sf
from utils.audio_processor import AudioProcessor

# Generate test audio
audio = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 2, 96000))
audio = audio.astype(np.float32)
sf.write("/tmp/test.wav", audio, 48000)

# Process audio
processor = AudioProcessor(target_sample_rate=48000)
processor.initialize()
result = processor.process_file("/tmp/test.wav", "/tmp/output.wav")

print("Test result:", "PASSED" if result['success'] else "FAILED")
print("Details:", result)
EOF
```

### Local Testing (if running backend locally)
```bash
cd tests
python test_audio_processing.py
```

## Test Output

Successful test output should show:
```
============================================================
AUDIO PROCESSING INTEGRATION TEST
============================================================

Step 1: Generating test audio file...
✓ Generated test audio: ...

Step 2: Initializing AudioProcessor...
✓ AudioProcessor initialized successfully

Step 3: Loading audio file...
✓ Audio loaded successfully

Step 4: Enhancing audio with DeepFilterNet...
✓ Audio enhanced successfully

Step 5: Saving enhanced audio...
✓ Enhanced audio saved to: ...

Step 6: Verifying output file...
✓ Output file exists

Step 7: Testing complete pipeline (process_file)...
✓ Complete pipeline test PASSED

============================================================
ALL TESTS PASSED ✓
============================================================
```

## Test Audio Specifications

- **Format:** WAV (uncompressed)
- **Duration:** 2 seconds
- **Sample Rate:** 48000 Hz
- **Channels:** 1 (mono)
- **Bit Depth:** 32-bit float
- **Content:** 440 Hz sine wave (musical note A4) with added Gaussian noise

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure all dependencies are installed
2. **Model download errors**: Ensure `git` is installed and internet is available
3. **CUDA errors**: Tests run on CPU by default, GPU is not required
4. **Permission errors**: Ensure write permissions to `/tmp` directory

### Debug Mode

For verbose output, modify the test to include:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests
  run: |
    docker-compose up -d
    docker-compose exec -T worker1 python /tests/test_audio_processing.py
```

## Adding New Tests

To add new integration tests:

1. Create a new test file in this directory
2. Import required modules from `backend/utils/`
3. Follow the same structure as `test_audio_processing.py`
4. Document what the test validates
5. Update this README
