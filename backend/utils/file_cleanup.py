import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List

logger = logging.getLogger(__name__)

class FileCleanupManager:
    """Manages automatic deletion of old files"""

    def __init__(self, directories: List[Path], retention_seconds: int):
        self.directories = directories
        self.retention_seconds = retention_seconds

    def cleanup_old_files(self):
        """Remove files older than retention period"""
        current_time = time.time()
        cutoff_time = current_time - self.retention_seconds

        total_deleted = 0

        for directory in self.directories:
            if not directory.exists():
                continue

            try:
                for file_path in directory.iterdir():
                    if not file_path.is_file():
                        continue

                    # Check file modification time
                    file_mtime = file_path.stat().st_mtime

                    if file_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            total_deleted += 1
                            logger.info(f"Deleted old file: {file_path.name}")
                        except Exception as e:
                            logger.error(f"Error deleting file {file_path}: {e}")

            except Exception as e:
                logger.error(f"Error scanning directory {directory}: {e}")

        if total_deleted > 0:
            logger.info(f"Cleanup completed: {total_deleted} files deleted")

        return total_deleted

    def delete_file(self, file_path: Path) -> bool:
        """Delete a specific file"""
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    def get_file_age_seconds(self, file_path: Path) -> float:
        """Get file age in seconds"""
        if not file_path.exists():
            return 0
        current_time = time.time()
        file_mtime = file_path.stat().st_mtime
        return current_time - file_mtime

    def get_time_until_deletion(self, file_path: Path) -> int:
        """Get remaining seconds until file deletion"""
        age = self.get_file_age_seconds(file_path)
        remaining = self.retention_seconds - age
        return max(0, int(remaining))
