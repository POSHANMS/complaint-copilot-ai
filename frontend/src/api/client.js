import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = axios.create({ baseURL: BASE_URL });

/** Health check */
export const healthCheck = () => apiClient.get('/health').then(r => r.data);

/**
 * POST /complaints/extract (SSE Stream)
 * Accepts either a File object or a rawText string.
 * Calls onEvent({ node, status, progress, label, partial_state, complaint_id, final_state }) as SSE events arrive.
 */
export async function apiExtractComplaintStream({ file, rawText, onEvent }) {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  } else if (rawText) {
    formData.append('raw_text', rawText);
  } else {
    throw new Error('Either file or rawText must be provided.');
  }

  const response = await fetch(`${BASE_URL}/complaints/extract?stream=true`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Server status ${response.status}: ${errText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalResult = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split('\n\n');
    buffer = frames.pop(); // Retain incomplete chunk

    for (const frame of frames) {
      if (!frame.trim()) continue;

      let eventName = 'message';
      let dataStr = '';

      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          dataStr = line.slice(5).trim();
        }
      }

      if (dataStr) {
        try {
          const parsed = JSON.parse(dataStr);
          if (onEvent) {
            onEvent(eventName, parsed);
          }
          if (eventName === 'complete') {
            finalResult = parsed;
          }
        } catch (e) {
          console.warn('Failed to parse SSE JSON frame:', dataStr, e);
        }
      }
    }
  }

  return finalResult;
}

/** Fallback non-streaming extraction */
export async function apiExtractComplaint({ file, rawText }) {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  } else if (rawText) {
    formData.append('raw_text', rawText);
  } else {
    throw new Error('Either file or rawText must be provided.');
  }

  const response = await apiClient.post('/complaints/extract?stream=false', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}
