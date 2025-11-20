"""
Integration test for audio processing pipeline

This test creates a sample audio file, processes it through the
DeepFilterNet enhancement pipeline, and verifies the output.
"""

import os
import sys
import numpy as np
import soundfile as sf
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from utils.audio_processor import AudioProcessor


def generate_test_audio(output_path: str, duration: float = 2.0, sample_rate: int = 48000):
    """
    Generate a test audio file with a sine wave and some noise

    Args:
        output_path: Path to save the test audio file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
    """
    # Create time array
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Generate a 440 Hz sine wave (A note)
    frequency = 440.0
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)

    # Add some noise to make it more realistic
    noise = 0.05 * np.random.randn(len(t))
    audio = audio + noise

    # Ensure audio is in float32 format
    audio = audio.astype(np.float32)

    # Save the audio file
    sf.write(output_path, audio, sample_rate)
    print(f"✓ Generated test audio: {output_path}")
    print(f"  Duration: {duration}s")
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Samples: {len(audio)}")
    return audio


def test_audio_processing():
    """Test the complete audio processing pipeline"""

    # Setup paths
    test_dir = Path(__file__).parent
    test_audio_dir = test_dir / "test_audio"
    test_audio_dir.mkdir(exist_ok=True)

    input_path = test_audio_dir / "test_input.wav"
    output_path = test_audio_dir / "test_output.wav"

    print("\n" + "="*60)
    print("AUDIO PROCESSING INTEGRATION TEST")
    print("="*60 + "\n")

    try:
        # Step 1: Generate test audio
        print("Step 1: Generating test audio file...")
        original_audio = generate_test_audio(str(input_path))

        # Step 2: Initialize audio processor
        print("\nStep 2: Initializing AudioProcessor...")
        processor = AudioProcessor(target_sample_rate=48000)
        processor.initialize()
        print("✓ AudioProcessor initialized successfully")

        # Step 3: Load audio
        print("\nStep 3: Loading audio file...")
        audio, sr = processor.load_audio(str(input_path))
        print(f"✓ Audio loaded successfully")
        print(f"  Shape: {audio.shape}")
        print(f"  Sample rate: {sr} Hz")
        print(f"  Data type: {audio.dtype}")
        print(f"  Min value: {audio.min():.4f}")
        print(f"  Max value: {audio.max():.4f}")

        # Step 4: Enhance audio
        print("\nStep 4: Enhancing audio with DeepFilterNet...")
        enhanced = processor.enhance_audio(audio, sr)
        print(f"✓ Audio enhanced successfully")
        print(f"  Output shape: {enhanced.shape}")
        print(f"  Output data type: {enhanced.dtype}")
        print(f"  Output min value: {enhanced.min():.4f}")
        print(f"  Output max value: {enhanced.max():.4f}")

        # Step 5: Save enhanced audio
        print("\nStep 5: Saving enhanced audio...")
        processor.save_audio(enhanced, str(output_path), sr)
        print(f"✓ Enhanced audio saved to: {output_path}")

        # Step 6: Verify output file
        print("\nStep 6: Verifying output file...")
        if not output_path.exists():
            raise Exception("Output file was not created")

        output_size = output_path.stat().st_size
        print(f"✓ Output file exists")
        print(f"  File size: {output_size} bytes ({output_size / 1024:.2f} KB)")

        # Step 7: Test complete pipeline
        print("\nStep 7: Testing complete pipeline (process_file)...")
        result = processor.process_file(str(input_path), str(output_path))

        if result['success']:
            print("✓ Complete pipeline test PASSED")
            print(f"  Duration: {result['duration_seconds']:.2f}s")
            print(f"  Sample rate: {result['sample_rate']} Hz")
            print(f"  Output size: {result['output_size_mb']:.2f} MB")
        else:
            print(f"✗ Pipeline test FAILED: {result.get('error')}")
            return False

        # Final validation
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup - optionally remove test files
        # Uncomment to clean up after test
        # if input_path.exists():
        #     input_path.unlink()
        # if output_path.exists():
        #     output_path.unlink()
        pass


if __name__ == "__main__":
    success = test_audio_processing()
    sys.exit(0 if success else 1)
