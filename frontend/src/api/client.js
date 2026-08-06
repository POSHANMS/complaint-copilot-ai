import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = axios.create({ baseURL: BASE_URL });

/** Health check */
export const healthCheck = () => apiClient.get('/health').then(r => r.data);

/**
 * POST /complaints/extract
 * Accepts either a File object (for PDF/DOCX/TXT upload) or a rawText string.
 * Returns: { status, input_type, extracted_fields, summary, errors }
 */
export async function apiExtractComplaint({ file, rawText }) {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  } else if (rawText) {
    formData.append('raw_text', rawText);
  } else {
    throw new Error('Either file or rawText must be provided.');
  }

  const response = await apiClient.post('/complaints/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}
