"""
Unit tests for file handler utilities
"""
import pytest
from pathlib import Path
from utils.file_handler import FileHandler


class TestFileHandler:
    """Test FileHandler class"""

    @pytest.fixture
    def file_handler(self):
        """Create FileHandler instance"""
        return FileHandler(
            max_size_bytes=50 * 1024 * 1024,  # 50MB
            allowed_extensions={'mp3', 'wav', 'ogg', 'm4a', 'flac'}
        )

    def test_validate_file_extension_valid(self, file_handler):
        """Test validation of valid file extensions"""
        valid_files = [
            "audio.mp3",
            "song.wav",
            "music.ogg",
            "track.m4a",
            "recording.flac"
        ]

        for filename in valid_files:
            is_valid, error = file_handler.validate_file_extension(filename)
            assert is_valid is True
            assert error is None

    def test_validate_file_extension_invalid(self, file_handler):
        """Test validation of invalid file extensions"""
        invalid_files = [
            "document.pdf",
            "video.mp4",
            "script.py",
            "noextension"
        ]

        for filename in invalid_files:
            is_valid, error = file_handler.validate_file_extension(filename)
            assert is_valid is False
            assert error is not None
            assert "not allowed" in error or "Invalid file type" in error

    def test_validate_file_extension_case_insensitive(self, file_handler):
        """Test that file extension validation is case-insensitive"""
        filenames = ["audio.MP3", "audio.Wav", "audio.OGG"]

        for filename in filenames:
            is_valid, error = file_handler.validate_file_extension(filename)
            assert is_valid is True
            assert error is None

    def test_validate_file_size_within_limit(self, file_handler):
        """Test validation of file size within limit"""
        sizes = [
            1024,  # 1KB
            1024 * 1024,  # 1MB
            10 * 1024 * 1024,  # 10MB
            50 * 1024 * 1024 - 1  # Just under 50MB
        ]

        for size in sizes:
            is_valid, error = file_handler.validate_file_size(size)
            assert is_valid is True
            assert error is None

    def test_validate_file_size_exceeds_limit(self, file_handler):
        """Test validation of file size exceeding limit"""
        sizes = [
            50 * 1024 * 1024 + 1,  # Just over 50MB
            100 * 1024 * 1024,  # 100MB
            1024 * 1024 * 1024  # 1GB
        ]

        for size in sizes:
            is_valid, error = file_handler.validate_file_size(size)
            assert is_valid is False
            assert error is not None
            assert "exceeds maximum" in error

    def test_generate_unique_filename(self, file_handler):
        """Test unique filename generation"""
        original_filename = "audio.mp3"

        # Generate multiple unique filenames
        filenames = [
            file_handler.generate_unique_filename(original_filename)
            for _ in range(10)
        ]

        # All filenames should be unique
        assert len(filenames) == len(set(filenames))

        # All filenames should preserve the original extension
        for filename in filenames:
            assert filename.endswith(".mp3")

        # Filenames should contain a UUID
        for filename in filenames:
            assert len(filename) > len(original_filename)

    def test_validate_mime_type_valid(self, file_handler, sample_audio_file):
        """Test MIME type validation for valid audio file"""
        is_valid, error = file_handler.validate_mime_type(str(sample_audio_file))
        assert is_valid is True
        assert error is None

    def test_validate_mime_type_invalid(self, file_handler, temp_dir):
        """Test MIME type validation for invalid file"""
        # Create a fake audio file with text content
        fake_audio = temp_dir / "fake.mp3"
        fake_audio.write_text("This is not audio")

        is_valid, error = file_handler.validate_mime_type(str(fake_audio))
        # Should fail MIME type check (it's text, not audio)
        assert is_valid is False or error is not None
