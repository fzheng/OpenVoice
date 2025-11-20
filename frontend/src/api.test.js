import { describe, it, expect, vi, beforeEach } from 'vitest';
import { uploadAudio, getTaskStatus, downloadAudio, deleteFiles } from './api';

// Mock axios - must be inline in vi.mock due to hoisting
vi.mock('axios', () => {
  const mockAxiosInstance = {
    post: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
  };

  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      post: vi.fn(),
      get: vi.fn(),
      delete: vi.fn(),
    },
  };
});

// Import the mocked axios after the mock is set up
import axios from 'axios';

// Get reference to the mocked axios instance
const api = axios.create();

describe('API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('uploadAudio', () => {
    it('sends POST request with file and noise_strength', async () => {
      const mockResponse = {
        data: {
          task_id: 'test-123',
          filename: 'test.mp3',
        },
      };

      api.post.mockResolvedValue(mockResponse);

      const file = new File(['audio data'], 'test.mp3', { type: 'audio/mpeg' });
      const noiseStrength = 7;
      const onProgress = vi.fn();

      const result = await uploadAudio(file, noiseStrength, onProgress);

      expect(api.post).toHaveBeenCalledWith(
        expect.stringContaining('/api/upload'),
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      expect(result).toEqual(mockResponse.data);
    });

    it('includes noise_strength in FormData', async () => {
      api.post.mockResolvedValue({ data: { task_id: 'test' } });

      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' });
      const noiseStrength = 5;

      await uploadAudio(file, noiseStrength);

      const formData = api.post.mock.calls[0][1];
      expect(formData.get('noise_strength')).toBe('5');
      expect(formData.get('file')).toBe(file);
    });

    it('calls onProgress callback during upload', async () => {
      api.post.mockImplementation((url, data, config) => {
        // Simulate progress
        config.onUploadProgress({ loaded: 50, total: 100 });
        return Promise.resolve({ data: { task_id: 'test' } });
      });

      const onProgress = vi.fn();
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' });

      await uploadAudio(file, 7, onProgress);

      expect(onProgress).toHaveBeenCalledWith({ loaded: 50, total: 100 });
    });
  });

  describe('getTaskStatus', () => {
    it('sends GET request to status endpoint', async () => {
      const mockResponse = {
        data: {
          task_id: 'test-123',
          status: 'processing',
          progress: 50,
        },
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await getTaskStatus('test-123');

      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/status/test-123')
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('downloadAudio', () => {
    it('sends GET request with blob response type', async () => {
      const mockBlob = new Blob(['audio data'], { type: 'audio/wav' });
      const mockResponse = { data: mockBlob };

      api.get.mockResolvedValue(mockResponse);

      const result = await downloadAudio('test-123');

      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/download/test-123'),
        expect.objectContaining({
          responseType: 'blob',
        })
      );
      expect(result).toBe(mockBlob);
    });
  });

  describe('deleteFiles', () => {
    it('sends DELETE request to delete endpoint', async () => {
      const mockResponse = {
        data: {
          success: true,
          task_id: 'test-123',
        },
      };

      api.delete.mockResolvedValue(mockResponse);

      const result = await deleteFiles('test-123');

      expect(api.delete).toHaveBeenCalledWith(
        expect.stringContaining('/api/delete/test-123')
      );
      expect(result).toEqual(mockResponse.data);
    });
  });
});
