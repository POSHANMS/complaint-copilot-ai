import { useDispatch } from 'react';
import { apiExtractComplaintStream } from '../api/client';
import { setExtracting, setProgress } from '../store/slices/uiSlice';
import {
  setAllFieldsLoading,
  setAllFieldsEmpty,
  setSingleField,
  processNodeStreamUpdate
} from '../store/slices/complaintSlice';
import { fetchSuggestions, clearChat } from '../store/slices/chatSlice';

export function useExtractionStream() {
  const dispatch = useDispatch();

  const startExtraction = async ({ file, rawText }) => {
    try {
      dispatch(setExtracting(true));
      dispatch(clearChat());
      dispatch(setAllFieldsLoading());
      dispatch(setProgress({ progress: 5, statusText: 'Connecting to LangGraph SSE Stream...' }));

      await apiExtractComplaintStream({
        file,
        rawText,
        onEvent: (eventName, data) => {
          if (eventName === 'node_complete') {
            const { node, progress, label, partial_state } = data;
            
            // 1. Update UI progress & real node status text
            dispatch(setProgress({ progress, statusText: label || `Completed ${node}` }));

            // 2. Dispatch real partial state update to Redux complaint slice
            dispatch(processNodeStreamUpdate({ node, partial_state }));

          } else if (eventName === 'complete') {
            const { progress, label, complaint_id, final_state } = data;
            
            dispatch(setProgress({ progress: 100, statusText: label || 'Extraction complete!' }));
            dispatch(processNodeStreamUpdate({ node: 'END', complaint_id, final_state }));
            
            if (complaint_id) {
              dispatch(fetchSuggestions(complaint_id));
            }
            dispatch(setExtracting(false));
          } else if (eventName === 'error') {
            dispatch(setExtracting(false));
            dispatch(setAllFieldsEmpty());
            throw new Error(data.error || 'Pipeline execution failed');
          }
        }
      });

    } catch (err) {
      dispatch(setExtracting(false));
      dispatch(setAllFieldsEmpty());
      console.error('Streaming extraction error:', err);
      throw err;
    }
  };

  return { startExtraction };
}
