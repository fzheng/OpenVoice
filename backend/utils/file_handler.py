import os
import uuid
import magic
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FileHandler:
    """Handles file upload validation and management"""

    ALLOWED_MIME_TYPES = {
        'audio/mpeg',           # MP3
        'audio/wav',            # WAV
        'audio/x-wav',          # WAV alternative
        'audio/wave',           # WAV alternative
        'audio/ogg',            # OGG
        'audio/x-m4a',          # M4A
        'audio/mp4',            # M4A/MP4
        'audio/flac',           # FLAC
        'audio/x-flac',         # FLAC alternative
        'audio/aac',            # AAC
        'audio/x-ms-wma',       # WMA
    }

    def __init__(self, max_size_bytes: int, allowed_extensions: set):
        self.max_size_bytes = max_size_bytes
        self.allowed_extensions = allowed_extensions
        self.mime = magic.Magic(mime=True)

    def validate_file_size(self, file_size: int) -> Tuple[bool, Optional[str]]:
        """Validate file size"""
        if file_size > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size of {max_mb}MB"
        return True, None

    def validate_file_extension(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate file extension"""
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in self.allowed_extensions:
            return False, f"File extension '.{ext}' not allowed. Allowed: {', '.join(self.allowed_extensions)}"
        return True, None

    def validate_mime_type(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate MIME type"""
        try:
            mime_type = self.mime.from_file(file_path)
            if mime_type not in self.ALLOWED_MIME_TYPES:
                return False, f"Invalid file type. Expected audio file, got {mime_type}"
            return True, None
        except Exception as e:
            logger.error(f"Error validating MIME type: {e}")
            return False, f"Error validating file type: {str(e)}"

    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename"""
        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'bin'
        unique_id = uuid.uuid4().hex
        return f"{unique_id}.{ext}"

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        return os.path.getsize(file_path)


class VirusScanner:
    """Handles virus scanning of uploaded files"""

    def __init__(self, enabled: bool = False, clamav_host: str = 'localhost', clamav_port: int = 3310):
        self.enabled = enabled
        self.clamav_host = clamav_host
        self.clamav_port = clamav_port
        self.clamd = None

        if self.enabled:
            try:
                import pyclamd
                self.clamd = pyclamd.ClamdNetworkSocket(host=clamav_host, port=clamav_port)
                # Test connection
                if not self.clamd.ping():
                    logger.warning("ClamAV daemon not responding. Virus scanning disabled.")
                    self.enabled = False
            except ImportError:
                logger.warning("pyclamd not installed. Virus scanning disabled.")
                self.enabled = False
            except Exception as e:
                logger.warning(f"Failed to initialize ClamAV: {e}. Virus scanning disabled.")
                self.enabled = False

    def scan_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Scan file for viruses

        Returns:
            Tuple[bool, Optional[str]]: (is_clean, error_message)
        """
        if not self.enabled:
            # If scanning is disabled, consider all files clean
            return True, None

        try:
            result = self.clamd.scan_file(file_path)

            if result is None:
                # File is clean
                return True, None
            else:
                # Virus detected
                virus_name = result[file_path][1] if file_path in result else "Unknown"
                logger.warning(f"Virus detected in {file_path}: {virus_name}")
                return False, f"Virus detected: {virus_name}"

        except Exception as e:
            logger.error(f"Error scanning file: {e}")
            # In case of error, fail safe by rejecting the file
            return False, f"Error scanning file: {str(e)}"
