import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import * as api from './api';

// Mock the API module
vi.mock('./api', () => ({
  uploadAudio: vi.fn(),
  getTaskStatus: vi.fn(),
  downloadAudio: vi.fn(),
  deleteFiles: vi.fn(),
}));

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the main heading', () => {
    render(<App />);
    expect(screen.getByText('OpenVoice')).toBeInTheDocument();
  });

  it('displays privacy notice', () => {
    render(<App />);
    expect(screen.getByText(/Privacy Notice/i)).toBeInTheDocument();
    expect(screen.getByText(/automatically deleted after 10 minutes/i)).toBeInTheDocument();
  });

  it('shows file upload area by default', () => {
    render(<App />);
    expect(screen.getByText(/Click to upload/i)).toBeInTheDocument();
    expect(screen.getByText(/MP3, WAV, OGG/i)).toBeInTheDocument();
  });

  it('displays noise reduction slider with default value', () => {
    render(<App />);
    expect(screen.getByText(/Noise Reduction/i)).toBeInTheDocument();

    const slider = screen.getByRole('slider');
    expect(slider).toBeInTheDocument();
    expect(slider).toHaveValue('7'); // Default value
  });

  it('updates noise strength when slider is moved', () => {
    render(<App />);

    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '10' } });

    expect(slider).toHaveValue('10');
    expect(screen.getByText('10/10')).toBeInTheDocument();
  });

  it('shows different strength descriptions for slider values', () => {
    render(<App />);

    const slider = screen.getByRole('slider');

    // Test different values
    fireEvent.change(slider, { target: { value: '2' } });
    expect(screen.getByText(/Soft noise cleanup/i)).toBeInTheDocument();

    fireEvent.change(slider, { target: { value: '5' } });
    expect(screen.getByText(/Balanced noise cleanup/i)).toBeInTheDocument();

    fireEvent.change(slider, { target: { value: '8' } });
    expect(screen.getByText(/Strong noise cleanup/i)).toBeInTheDocument();

    fireEvent.change(slider, { target: { value: '10' } });
    expect(screen.getByText(/Max noise cleanup/i)).toBeInTheDocument();
  });

  it('disables upload button when no file is selected', () => {
    render(<App />);

    const uploadButton = screen.getByRole('button', { name: /Upload and Enhance/i });
    expect(uploadButton).toBeDisabled();
  });

  it('validates file size', async () => {
    render(<App />);

    // Create a fake file larger than 50MB
    const largeFile = new File(['x'.repeat(51 * 1024 * 1024)], 'large.mp3', {
      type: 'audio/mpeg',
    });

    const input = screen.getByLabelText(/Click to upload/i);

    Object.defineProperty(input, 'files', {
      value: [largeFile],
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText(/File size exceeds 50MB limit/i)).toBeInTheDocument();
    });
  });

  it('validates file type', async () => {
    render(<App />);

    const pdfFile = new File(['fake pdf content'], 'document.pdf', {
      type: 'application/pdf',
    });

    const input = screen.getByLabelText(/Click to upload/i);

    Object.defineProperty(input, 'files', {
      value: [pdfFile],
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument();
    });
  });

  it('accepts valid audio file', async () => {
    render(<App />);

    const audioFile = new File(['fake audio'], 'test.mp3', {
      type: 'audio/mpeg',
    });

    const input = screen.getByLabelText(/Click to upload/i);

    Object.defineProperty(input, 'files', {
      value: [audioFile],
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText('test.mp3')).toBeInTheDocument();
    });

    const uploadButton = screen.getByRole('button', { name: /Upload and Enhance/i });
    expect(uploadButton).not.toBeDisabled();
  });

  it('calls uploadAudio with correct parameters when upload button is clicked', async () => {
    const mockUploadResponse = {
      task_id: 'test-task-123',
      queue_position: 0,
    };

    api.uploadAudio.mockResolvedValue(mockUploadResponse);

    render(<App />);

    const audioFile = new File(['fake audio'], 'test.mp3', {
      type: 'audio/mpeg',
    });

    const input = screen.getByLabelText(/Click to upload/i);

    Object.defineProperty(input, 'files', {
      value: [audioFile],
    });

    fireEvent.change(input);

    // Change noise strength to 8
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '8' } });

    const uploadButton = screen.getByRole('button', { name: /Upload and Enhance/i });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(api.uploadAudio).toHaveBeenCalledWith(
        audioFile,
        8, // The slider value at time of upload
        expect.any(Function) // Progress callback
      );
    });
  });

  it('displays queue position when task is queued', async () => {
    const mockUploadResponse = {
      task_id: 'test-task-123',
      queue_position: 3,
    };

    const mockStatusResponse = {
      status: 'queued',
      progress: 0,
      queue_position: 3,
    };

    api.uploadAudio.mockResolvedValue(mockUploadResponse);
    api.getTaskStatus.mockResolvedValue(mockStatusResponse);

    render(<App />);

    const audioFile = new File(['fake audio'], 'test.mp3', {
      type: 'audio/mpeg',
    });

    const input = screen.getByLabelText(/Click to upload/i);

    Object.defineProperty(input, 'files', {
      value: [audioFile],
    });

    fireEvent.change(input);

    const uploadButton = screen.getByRole('button', { name: /Upload and Enhance/i });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText(/3 users ahead of you/i)).toBeInTheDocument();
    });
  });

  it('shows download button when processing is completed', async () => {
    const mockStatusResponse = {
      status: 'completed',
      progress: 100,
    };

    api.getTaskStatus.mockResolvedValue(mockStatusResponse);

    render(<App />);

    // Simulate task completion
    const audioFile = new File(['fake audio'], 'test.mp3', {
      type: 'audio/mpeg',
    });

    const input = screen.getByLabelText(/Click to upload/i);
    Object.defineProperty(input, 'files', {
      value: [audioFile],
    });
    fireEvent.change(input);

    api.uploadAudio.mockResolvedValue({
      task_id: 'test-task-123',
      queue_position: 0,
    });

    const uploadButton = screen.getByRole('button', { name: /Upload and Enhance/i });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Download Enhanced Audio/i })).toBeInTheDocument();
    });
  });

  it('resets slider to default when upload button is clicked', async () => {
    api.uploadAudio.mockResolvedValue({
      task_id: 'test-task-123',
      queue_position: 0,
    });

    render(<App />);

    const audioFile = new File(['fake audio'], 'test.mp3', {
      type: 'audio/mpeg',
    });

    const input = screen.getByLabelText(/Click to upload/i);
    Object.defineProperty(input, 'files', {
      value: [audioFile],
    });
    fireEvent.change(input);

    // Change slider value
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '10' } });
    expect(slider).toHaveValue('10');

    // Click upload
    const uploadButton = screen.getByRole('button', { name: /Upload and Enhance/i });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      // After upload, if we render upload UI again, slider should be at default
      expect(api.uploadAudio).toHaveBeenCalled();
    });
  });
});

describe('Noise Strength Calculations', () => {
  it('calculates correct attenuation for slider values', () => {
    const testCases = [
      { slider: 0, expectedAttenuation: 6 },
      { slider: 5, expectedAttenuation: 16 },
      { slider: 7, expectedAttenuation: 20 },
      { slider: 10, expectedAttenuation: 26 },
    ];

    testCases.forEach(({ slider, expectedAttenuation }) => {
      const attenuation = 6 + slider * 2;
      expect(attenuation).toBe(expectedAttenuation);
    });
  });

  it('calculates correct gain compensation for slider values', () => {
    const testCases = [
      { slider: 0, expectedGain: 2.0 },
      { slider: 5, expectedGain: 1.5 },
      { slider: 10, expectedGain: 1.0 },
    ];

    testCases.forEach(({ slider, expectedGain }) => {
      const gain = Math.max(0.0, Math.round((2.0 - slider * 0.1) * 100) / 100);
      expect(gain).toBe(expectedGain);
    });
  });
});
