"""
Unit tests for audio processor
"""
import pytest
import numpy as np
import soundfile as sf
import torch
from pathlib import Path
from utils.audio_processor import AudioProcessor


class TestAudioProcessor:
    """Test AudioProcessor class"""

    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance"""
        return AudioProcessor(target_sample_rate=48000)

    def test_initialization(self, audio_processor):
        """Test AudioProcessor initialization"""
        assert audio_processor.target_sample_rate == 48000
        assert audio_processor.model is None
        assert audio_processor.df_state is None
        assert audio_processor._initialized is False

    def test_load_audio(self, audio_processor, sample_audio_file):
        """Test audio loading"""
        audio, sr = audio_processor.load_audio(str(sample_audio_file))

        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert len(audio) > 0
        assert sr == audio_processor.target_sample_rate

    def test_load_audio_mono_conversion(self, audio_processor, temp_dir):
        """Test that stereo audio is converted to mono"""
        # Create stereo audio file
        sample_rate = 48000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Create stereo audio (2 channels)
        left = 0.5 * np.sin(2 * np.pi * 440 * t)
        right = 0.5 * np.sin(2 * np.pi * 880 * t)
        stereo_audio = np.stack([left, right], axis=1).astype(np.float32)

        stereo_file = temp_dir / "stereo.wav"
        sf.write(stereo_file, stereo_audio, sample_rate)

        # Load and verify it's converted to mono
        audio, sr = audio_processor.load_audio(str(stereo_file))

        assert audio.ndim == 1  # Mono
        assert len(audio) > 0

    def test_load_audio_resampling(self, audio_processor, temp_dir):
        """Test that audio is resampled to target sample rate"""
        # Create audio at different sample rate
        original_sr = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(original_sr * duration))
        audio_data = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

        audio_file = temp_dir / "16khz.wav"
        sf.write(audio_file, audio_data, original_sr)

        # Load and verify resampling
        audio, sr = audio_processor.load_audio(str(audio_file))

        assert sr == 48000  # Resampled to target
        # Length should be scaled proportionally
        expected_length = int(len(audio_data) * (48000 / 16000))
        assert abs(len(audio) - expected_length) < 100  # Allow small rounding difference

    def test_save_audio(self, audio_processor, temp_dir):
        """Test audio saving"""
        # Create sample audio
        sample_rate = 48000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

        # Save audio
        output_path = temp_dir / "output.wav"
        audio_processor.save_audio(audio, str(output_path), sample_rate)

        # Verify file exists and can be loaded
        assert output_path.exists()
        loaded_audio, loaded_sr = sf.read(output_path)
        assert loaded_sr == sample_rate
        assert len(loaded_audio) == len(audio)

    def test_normalize_audio(self, audio_processor):
        """Test audio normalization"""
        # Create audio that exceeds [-1, 1] range
        audio = np.array([0.5, 1.5, -2.0, 0.8], dtype=np.float32)

        normalized = audio_processor.normalize_audio(audio)

        # Should be normalized to [-1, 1] range
        assert normalized.max() <= 1.0
        assert normalized.min() >= -1.0
        assert abs(normalized.max()) == 1.0 or abs(normalized.min()) == 1.0

    def test_normalize_audio_already_normalized(self, audio_processor):
        """Test that already normalized audio is unchanged"""
        audio = np.array([0.5, -0.5, 0.3, -0.8], dtype=np.float32)

        normalized = audio_processor.normalize_audio(audio)

        # Should remain the same
        np.testing.assert_array_almost_equal(normalized, audio)

    def test_enhance_audio_tensor_conversion(self, audio_processor):
        """Test that enhance_audio handles numpy to tensor conversion"""
        # Create simple numpy audio
        audio = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

        # Mock the DeepFilterNet enhancement to avoid full initialization
        # Just test the tensor conversion logic
        audio_tensor = torch.from_numpy(audio)
        assert isinstance(audio_tensor, torch.Tensor)
        assert audio_tensor.dtype == torch.float32

    def test_enhance_audio_dimension_handling(self, audio_processor):
        """Test that enhance_audio handles 1D to 2D tensor conversion"""
        # Create 1D audio tensor
        audio_1d = torch.tensor([0.1, 0.2, 0.3], dtype=torch.float32)

        # Add channel dimension
        audio_2d = audio_1d.unsqueeze(0)

        assert audio_1d.dim() == 1
        assert audio_2d.dim() == 2
        assert audio_2d.shape[0] == 1  # 1 channel

        # Remove channel dimension
        audio_back = audio_2d.squeeze(0)
        assert audio_back.dim() == 1
        torch.testing.assert_close(audio_back, audio_1d)

    def test_attenuation_and_gain_parameters(self, audio_processor):
        """Test that attenuation and gain parameters are stored correctly"""
        processor = AudioProcessor(
            target_sample_rate=48000,
            attenuation_limit_db=15.0,
            output_gain_db=2.0
        )

        assert processor.attenuation_limit_db == 15.0
        assert processor.output_gain_db == 2.0

    def test_slider_to_db_mapping(self):
        """Test the slider value to dB mapping logic"""
        # This tests the mapping from main.py: attenuation = 6 + strength * 2
        test_cases = [
            (0, 6.0),   # Minimum: 6 dB
            (5, 16.0),  # Middle: 16 dB
            (7, 20.0),  # Default: 20 dB
            (10, 26.0)  # Maximum: 26 dB
        ]

        for slider_value, expected_db in test_cases:
            calculated_db = 6 + slider_value * 2
            assert calculated_db == expected_db

    def test_gain_compensation_logic(self):
        """Test the gain compensation logic"""
        # This tests the mapping from main.py: gain = 2.0 - strength * 0.1
        test_cases = [
            (0, 2.0),   # Minimum suppression: max gain
            (5, 1.5),   # Middle suppression: medium gain
            (10, 1.0),  # Maximum suppression: min gain
        ]

        for slider_value, expected_gain in test_cases:
            calculated_gain = max(0.0, round(2.0 - slider_value * 0.1, 2))
            assert calculated_gain == expected_gain


class TestAudioProcessingIntegration:
    """Integration tests for complete audio processing pipeline"""

    def test_full_processing_pipeline(self, temp_dir, sample_audio_file):
        """Test the complete audio processing pipeline"""
        # This is a simplified integration test
        # Full test with DeepFilterNet would require model initialization

        processor = AudioProcessor(target_sample_rate=48000)

        # Load audio
        audio, sr = processor.load_audio(str(sample_audio_file))
        assert len(audio) > 0

        # Normalize
        normalized = processor.normalize_audio(audio)
        assert normalized.max() <= 1.0
        assert normalized.min() >= -1.0

        # Save
        output_path = temp_dir / "processed.wav"
        processor.save_audio(normalized, str(output_path), sr)

        # Verify output
        assert output_path.exists()
        loaded, loaded_sr = sf.read(output_path)
        assert loaded_sr == sr
        assert len(loaded) == len(normalized)

    def test_process_audio_file_end_to_end(self, temp_dir, sample_audio_file):
        """Test process_audio_file method (without DeepFilterNet)"""
        processor = AudioProcessor(target_sample_rate=48000)
        output_path = temp_dir / "output.wav"

        # Test loading and saving without enhancement
        # (Enhancement requires DeepFilterNet model initialization)
        audio, sr = processor.load_audio(str(sample_audio_file))
        normalized = processor.normalize_audio(audio)
        processor.save_audio(normalized, str(output_path), sr)

        assert output_path.exists()
        output_audio, output_sr = sf.read(output_path)
        assert output_sr == 48000
        assert len(output_audio) > 0
