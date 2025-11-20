import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for large file uploads
});

export const uploadAudio = async (file, noiseStrength, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  if (noiseStrength !== undefined && noiseStrength !== null) {
    formData.append('noise_strength', noiseStrength);
  }

  const response = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress,
  });

  return response.data;
};

export const getTaskStatus = async (taskId) => {
  const response = await api.get(`/api/status/${taskId}`);
  return response.data;
};

export const downloadAudio = async (taskId) => {
  const response = await api.get(`/api/download/${taskId}`, {
    responseType: 'blob',
  });
  return response.data;
};

export const deleteFiles = async (taskId) => {
  const response = await api.delete(`/api/delete/${taskId}`);
  return response.data;
};

export const getQueueStatus = async () => {
  const response = await api.get('/api/queue');
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

export default api;
