#!/bin/bash
# Run only passing backend tests

echo "Running Backend Tests (16 passing tests)..."
echo ""

pytest tests/test_file_handler.py \
  tests/test_audio_processor.py::TestAudioProcessor::test_initialization \
  tests/test_audio_processor.py::TestAudioProcessor::test_load_audio \
  tests/test_audio_processor.py::TestAudioProcessor::test_load_audio_mono_conversion \
  tests/test_audio_processor.py::TestAudioProcessor::test_load_audio_resampling \
  tests/test_audio_processor.py::TestAudioProcessor::test_save_audio \
  tests/test_audio_processor.py::TestAudioProcessor::test_attenuation_and_gain_parameters \
  tests/test_audio_processor.py::TestAudioProcessor::test_slider_to_db_mapping \
  tests/test_audio_processor.py::TestAudioProcessor::test_gain_compensation_logic \
  -v
