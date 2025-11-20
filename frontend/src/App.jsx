import React, { useState, useEffect } from 'react';
import { Upload, Download, Trash2, AlertCircle, CheckCircle, Loader, Music, Info } from 'lucide-react';
import { uploadAudio, getTaskStatus, downloadAudio, deleteFiles } from './api';

const MAX_FILE_SIZE_MB = 50;
const POLL_INTERVAL = 2000; // Poll every 2 seconds
const DEFAULT_NOISE_STRENGTH = 7; // Slider 0-10 (higher = stronger noise reduction)

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [queuePosition, setQueuePosition] = useState(0);
  const [noiseStrength, setNoiseStrength] = useState(DEFAULT_NOISE_STRENGTH);

  // Poll for task status
  useEffect(() => {
    if (!taskId) return;

    const pollStatus = async () => {
      try {
        const statusData = await getTaskStatus(taskId);
        setStatus(statusData);
        setQueuePosition(statusData.queue_position || 0);

        // Stop polling if task is completed or failed
        if (statusData.status === 'completed' || statusData.status === 'failed') {
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    };

    const intervalId = setInterval(pollStatus, POLL_INTERVAL);
    pollStatus(); // Initial poll

    return () => clearInterval(intervalId);
  }, [taskId]);

  const handleFileSelect = (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;

    // Validate file size
    const fileSizeMB = selectedFile.size / (1024 * 1024);
    if (fileSizeMB > MAX_FILE_SIZE_MB) {
      setError(`File size exceeds ${MAX_FILE_SIZE_MB}MB limit`);
      return;
    }

    // Validate file type
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4', 'audio/flac', 'audio/aac'];
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.match(/\.(mp3|wav|ogg|m4a|flac|aac|wma)$/i)) {
      setError('Invalid file type. Please upload an audio file.');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setTaskId(null);
    setStatus(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setUploadProgress(0);
    setNoiseStrength(DEFAULT_NOISE_STRENGTH);

    try {
      const result = await uploadAudio(file, noiseStrength, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      });

      setTaskId(result.task_id);
      setQueuePosition(result.queue_position || 0);
      setUploading(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      setUploading(false);
    }
  };

  const handleDownload = async () => {
    if (!taskId) return;

    try {
      const blob = await downloadAudio(taskId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `enhanced_${file.name}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err.response?.data?.detail || 'Download failed. Please try again.');
    }
  };

  const handleDelete = async () => {
    if (!taskId) return;

    try {
      await deleteFiles(taskId);
      // Reset state
      setFile(null);
      setTaskId(null);
      setStatus(null);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Delete failed. Please try again.');
    }
  };

  const handleReset = () => {
    setFile(null);
    setTaskId(null);
    setStatus(null);
    setError(null);
    setUploadProgress(0);
  };

  const getStatusColor = () => {
    if (!status) return 'bg-gray-200';
    switch (status.status) {
      case 'queued': return 'bg-yellow-500';
      case 'processing': return 'bg-blue-500';
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const describeStrength = (value) => {
    if (value <= 2) return 'Soft';
    if (value <= 5) return 'Balanced';
    if (value <= 8) return 'Strong';
    return 'Max';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Music className="w-12 h-12 text-primary-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-800">OpenVoice</h1>
          </div>
          <p className="text-lg text-gray-600">
            Remove background noise and enhance your voice with AI
          </p>
        </div>

        {/* Privacy Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-start">
          <Info className="w-5 h-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <strong>Privacy Notice:</strong> Your files are automatically deleted after 10 minutes.
            We do not store or persist your audio files beyond this period. All processing happens
            securely on our servers, and your data is never shared.
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5" />
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          {/* File Upload Section */}
          {!taskId && (
            <div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Audio File (Max {MAX_FILE_SIZE_MB}MB)
                </label>
                <div className="flex items-center justify-center w-full">
                  <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-10 h-10 mb-3 text-gray-400" />
                      <p className="mb-2 text-sm text-gray-500">
                        <span className="font-semibold">Click to upload</span> or drag and drop
                      </p>
                      <p className="text-xs text-gray-500">MP3, WAV, OGG, M4A, FLAC, AAC, WMA</p>
                    </div>
                    <input
                      type="file"
                      className="hidden"
                      accept="audio/*,.mp3,.wav,.ogg,.m4a,.flac,.aac,.wma"
                      onChange={handleFileSelect}
                      disabled={uploading}
                    />
                  </label>
                </div>
              </div>

              {/* Noise Reduction Slider */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Noise Reduction
                    <span className="ml-2 text-xs text-gray-500">(higher = stronger)</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setNoiseStrength(DEFAULT_NOISE_STRENGTH)}
                    className="text-xs text-primary-600 hover:text-primary-700 font-semibold"
                    disabled={uploading}
                  >
                    Reset
                  </button>
                </div>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="0"
                    max="10"
                    step="1"
                    value={noiseStrength}
                    onChange={(e) => setNoiseStrength(Number(e.target.value))}
                    className="w-full accent-primary-600"
                    disabled={uploading}
                  />
                  <div className="w-16 text-right text-sm font-semibold text-gray-800">
                    {noiseStrength}/10
                  </div>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  {describeStrength(noiseStrength)} noise cleanup. Stronger removes more noise but can affect quiet voices.
                </p>
              </div>

              {file && (
                <div className="mb-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Music className="w-5 h-5 text-gray-500 mr-2" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{file.name}</p>
                          <p className="text-xs text-gray-500">
                            {(file.size / (1024 * 1024)).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={handleReset}
                        className="text-gray-400 hover:text-gray-600"
                        disabled={uploading}
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {uploading && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Uploading...</span>
                    <span className="text-sm text-gray-600">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="w-full bg-primary-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                {uploading ? (
                  <>
                    <Loader className="animate-spin w-5 h-5 mr-2" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5 mr-2" />
                    Upload and Enhance
                  </>
                )}
              </button>
            </div>
          )}

          {/* Processing Status Section */}
          {taskId && status && (
            <div>
              {/* Status Header */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">Processing Status</h3>
                  {status.status === 'completed' && (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  )}
                  {status.status === 'processing' && (
                    <Loader className="w-6 h-6 text-blue-500 animate-spin" />
                  )}
                </div>

                {/* Queue Position */}
                {queuePosition > 0 && status.status === 'queued' && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                    <p className="text-sm text-yellow-800">
                      <strong>Queue Position:</strong> {queuePosition} {queuePosition === 1 ? 'user' : 'users'} ahead of you
                    </p>
                  </div>
                )}

                {/* Progress Bar */}
                <div className="mb-2">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {status.status === 'queued' ? 'In Queue' : status.status}
                    </span>
                    <span className="text-sm text-gray-600">{status.progress || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${getStatusColor()}`}
                      style={{ width: `${status.progress || 0}%` }}
                    />
                  </div>
                </div>

                {/* Completion Info */}
                {status.status === 'completed' && status.time_until_deletion_seconds && (
                  <div className="mt-4 text-sm text-gray-600">
                    <p>
                      File will be automatically deleted in:{' '}
                      <strong>{formatTime(status.time_until_deletion_seconds)}</strong>
                    </p>
                  </div>
                )}

                {/* Error Info */}
                {status.status === 'failed' && status.error && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-800">
                      <strong>Error:</strong> {status.error}
                    </p>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                {status.status === 'completed' && (
                  <button
                    onClick={handleDownload}
                    className="flex-1 bg-green-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Download Enhanced Audio
                  </button>
                )}

                <button
                  onClick={handleDelete}
                  className="flex-1 bg-red-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center"
                >
                  <Trash2 className="w-5 h-5 mr-2" />
                  Delete Files
                </button>

                <button
                  onClick={handleReset}
                  className="flex-1 bg-gray-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Upload New File
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>
            Powered by DeepFilterNet AI • Open Source • Privacy First
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
