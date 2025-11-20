import soundfile as sf
import librosa
import numpy as np
from pathlib import Path
import logging
import time
from typing import List, Optional, Tuple
import torch
import psutil
import os

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Handles audio processing using DeepFilterNet"""

    def __init__(
        self,
        target_sample_rate: int = 48000,
        max_chunk_duration: float = 30.0,
        chunk_overlap: float = 0.05,
        attenuation_limit_db: Optional[float] = None,
        output_gain_db: float = 0.0,
    ):
        self.target_sample_rate = target_sample_rate
        self.model = None
        self.df_state = None
        self._initialized = False
        # Chunking keeps memory usage bounded for long inputs
        self.max_chunk_samples = (
            int(max_chunk_duration * target_sample_rate) if max_chunk_duration and max_chunk_duration > 0 else None
        )
        self.chunk_overlap_samples = (
            int(chunk_overlap * target_sample_rate) if chunk_overlap and chunk_overlap > 0 else 0
        )
        self.attenuation_limit_db = attenuation_limit_db
        self.output_gain_db = output_gain_db

    def _log_memory_usage(self, stage: str):
        """Log current memory usage"""
        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            mem_mb = mem_info.rss / 1024 / 1024
            logger.info(f"Memory usage at {stage}: {mem_mb:.2f} MB")
        except Exception as e:
            logger.warning(f"Failed to log memory usage: {e}")

    def initialize(self):
        """Initialize DeepFilterNet model (lazy loading)"""
        if self._initialized:
            return

        try:
            self._log_memory_usage("before model initialization")
            logger.info("Initializing DeepFilterNet model...")
            from df import enhance, init_df

            # Retry a few times in case model download hits transient errors (e.g., GitHub 503)
            last_err = None
            for attempt in range(3):
                try:
                    self.model, self.df_state, _ = init_df()
                    self._initialized = True
                    break
                except SystemExit as se:
                    # init_df can call sys.exit on download failure; convert to recoverable error
                    last_err = RuntimeError(f"DeepFilterNet init aborted (SystemExit): {se}")
                except Exception as e:
                    last_err = e

                wait = 2 ** attempt
                logger.warning(f"DeepFilterNet init failed (attempt {attempt + 1}/3): {last_err}. Retrying in {wait}s...")
                time.sleep(wait)

            if not self._initialized:
                raise RuntimeError(f"Failed to initialize DeepFilterNet after retries: {last_err}")

            self._log_memory_usage("after model initialization")
            logger.info("DeepFilterNet model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DeepFilterNet: {e}")
            raise RuntimeError(f"Failed to initialize audio processing model: {str(e)}")

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file and resample if necessary

        Returns:
            Tuple[np.ndarray, int]: (audio_data, sample_rate)
        """
        try:
            # Load audio file
            audio, sr = librosa.load(file_path, sr=None, mono=False)

            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)

            # Resample to target sample rate if needed
            if sr != self.target_sample_rate:
                logger.info(f"Resampling from {sr}Hz to {self.target_sample_rate}Hz")
                audio = librosa.resample(
                    audio,
                    orig_sr=sr,
                    target_sr=self.target_sample_rate
                )
                sr = self.target_sample_rate

            return audio, sr

        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {e}")
            raise RuntimeError(f"Failed to load audio file: {str(e)}")

    def enhance_audio(
        self,
        audio: np.ndarray,
        sample_rate: int,
        attenuation_limit_db: Optional[float] = None,
        output_gain_db: Optional[float] = None,
    ) -> np.ndarray:
        """
        Enhance audio using DeepFilterNet

        Args:
            audio: Audio data as numpy array
            sample_rate: Sample rate of the audio

        Returns:
            Enhanced audio as numpy array
        """
        if not self._initialized:
            self.initialize()

        try:
            from df import enhance

            self._log_memory_usage("start of enhance_audio")

            # Ensure audio is in the correct format
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # Normalize audio to [-1, 1] range if needed
            if np.abs(audio).max() > 1.0:
                audio = audio / np.abs(audio).max()

            # Use overrides when provided, otherwise defaults from instance
            atten_lim = attenuation_limit_db if attenuation_limit_db is not None else self.attenuation_limit_db
            gain_db = output_gain_db if output_gain_db is not None else self.output_gain_db

            # Convert numpy array to PyTorch tensor for DeepFilterNet
            audio_tensor = torch.from_numpy(audio)

            # DeepFilterNet expects 2D tensor (channels, samples)
            # Add channel dimension if audio is 1D
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0)  # Shape: (1, samples)

            # Decide between full-buffer processing and chunked processing
            if self.max_chunk_samples and audio_tensor.shape[-1] > self.max_chunk_samples:
                logger.info(
                    f"Processing audio in chunks to manage memory: "
                    f"{self.max_chunk_samples / self.target_sample_rate:.1f}s per chunk"
                )
                enhanced_chunks: List[np.ndarray] = []
                overlap = min(self.chunk_overlap_samples, self.max_chunk_samples // 4)
                start = 0
                total_len = audio_tensor.shape[-1]
                chunk_idx = 1

                while start < total_len:
                    end = min(start + self.max_chunk_samples, total_len)
                    chunk_tensor = audio_tensor[..., start:end]
                    enhanced_chunk = self._run_enhance(
                        enhance, chunk_tensor, label=f"chunk {chunk_idx}", atten_lim_db=atten_lim
                    )
                    enhanced_chunks.append(enhanced_chunk)

                    if end >= total_len:
                        break

                    # step forward with overlap to reduce boundary artifacts
                    start = end - overlap if overlap > 0 else end
                    chunk_idx += 1

                enhanced = self._merge_chunks(enhanced_chunks, overlap)
            else:
                enhanced = self._run_enhance(enhance, audio_tensor, label="full", atten_lim_db=atten_lim)

            # Optional gentle gain lift post enhancement
            if gain_db and gain_db != 0:
                gain = 10 ** (gain_db / 20)
                enhanced = enhanced * gain
                # Avoid clipping: limit to [-1, 1]
                enhanced = np.clip(enhanced, -1.0, 1.0)

            self._log_memory_usage("end of enhance_audio")
            logger.info("Audio enhancement completed")
            return enhanced

        except Exception as e:
            logger.error(f"Error enhancing audio: {e}")
            raise RuntimeError(f"Failed to enhance audio: {str(e)}")

    def _run_enhance(self, enhance_fn, audio_tensor: torch.Tensor, label: str, atten_lim_db: Optional[float]) -> np.ndarray:
        """Run DeepFilterNet on a tensor and return 1D numpy audio."""
        self._log_memory_usage(f"before DeepFilterNet processing ({label})")

        # Process with DeepFilterNet
        logger.info(f"Processing audio with DeepFilterNet... ({label})")
        if atten_lim_db is not None:
            enhanced = enhance_fn(self.model, self.df_state, audio_tensor, atten_lim_db=atten_lim_db)
        else:
            enhanced = enhance_fn(self.model, self.df_state, audio_tensor)

        self._log_memory_usage(f"after DeepFilterNet processing ({label})")

        # Ensure output is numpy array
        if torch.is_tensor(enhanced):
            enhanced = enhanced.cpu().numpy()

        # Remove channel dimension if present (convert 2D back to 1D)
        if enhanced.ndim == 2 and enhanced.shape[0] == 1:
            enhanced = enhanced.squeeze(0)  # Shape: (samples,)

        return enhanced

    def _merge_chunks(self, chunks: List[np.ndarray], overlap_samples: int) -> np.ndarray:
        """Merge enhanced chunks with a small crossfade overlap to avoid clicks."""
        if not chunks:
            return np.array([], dtype=np.float32)

        if len(chunks) == 1 or overlap_samples <= 0:
            return np.concatenate(chunks).astype(np.float32)

        # Keep overlap modest and valid relative to chunk sizes
        safe_overlap = min(overlap_samples, min(len(c) for c in chunks) // 2)
        total_len = sum(len(c) for c in chunks) - safe_overlap * (len(chunks) - 1)
        output = np.zeros(total_len, dtype=np.float32)

        write_pos = 0
        for idx, chunk in enumerate(chunks):
            if idx == 0:
                output[: len(chunk)] = chunk
                write_pos = len(chunk)
                continue

            # Blend overlap
            start = write_pos - safe_overlap
            fade_len = safe_overlap
            if fade_len > 0:
                fade_in = np.linspace(0, 1, fade_len, dtype=np.float32)
                fade_out = 1.0 - fade_in
                output[start:write_pos] = output[start:write_pos] * fade_out + chunk[:fade_len] * fade_in

            remain = chunk[fade_len:]
            end = start + fade_len + len(remain)
            output[start + fade_len : end] = remain
            write_pos = end

        return output

    def save_audio(self, audio: np.ndarray, output_path: str, sample_rate: int) -> str:
        """Save enhanced audio to file, matching requested extension when possible."""
        try:
            target_path = Path(output_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            target_ext = target_path.suffix.lower()
            wav_path = target_path if target_ext == ".wav" else target_path.with_suffix(".wav")

            # Always write a WAV first (more reliable), then convert if needed
            sf.write(wav_path, audio, sample_rate, subtype="PCM_16")
            logger.info(f"Saved enhanced audio to {wav_path}")

            # Convert to target format if different
            if target_ext and target_ext != ".wav":
                try:
                    from pydub import AudioSegment

                    AudioSegment.from_file(wav_path, format="wav").export(
                        target_path, format=target_ext.lstrip(".")
                    )
                    size = target_path.stat().st_size if target_path.exists() else 0
                    if size > 0:
                        logger.info(f"Converted enhanced audio to {target_path} ({size} bytes)")
                        # Remove intermediate wav to save space
                        wav_path.unlink(missing_ok=True)
                        return str(target_path)
                    else:
                        logger.warning(
                            f"Conversion to {target_ext} produced empty file; keeping WAV instead"
                        )
                except Exception as conv_err:
                    logger.warning(
                        f"Failed to convert to {target_ext}; keeping WAV instead: {conv_err}"
                    )

            return str(wav_path)

        except Exception as e:
            logger.error(f"Error saving audio file {output_path}: {e}")
            raise RuntimeError(f"Failed to save audio file: {str(e)}")

    def process_file(
        self,
        input_path: str,
        output_path: str,
        attenuation_limit_db: Optional[float] = None,
        output_gain_db: Optional[float] = None,
    ) -> dict:
        """
        Process an audio file: load, enhance, and save

        Returns:
            Dictionary with processing statistics
        """
        try:
            # Load audio
            audio, sr = self.load_audio(input_path)

            original_duration = len(audio) / sr
            logger.info(f"Loaded audio: {original_duration:.2f}s at {sr}Hz")

            # Enhance audio
            enhanced = self.enhance_audio(
                audio,
                sr,
                attenuation_limit_db=attenuation_limit_db,
                output_gain_db=output_gain_db,
            )

            # Save enhanced audio (may return a different path if we fall back to wav)
            final_output_path = self.save_audio(enhanced, output_path, sr)

            # Get output file size
            output_size = Path(final_output_path).stat().st_size

            return {
                "success": True,
                "duration_seconds": original_duration,
                "sample_rate": sr,
                "output_size_bytes": output_size,
                "output_size_mb": output_size / (1024 * 1024),
                "output_path": final_output_path,
            }

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
