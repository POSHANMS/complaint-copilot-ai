import { configureStore } from '@reduxjs/toolkit';
import complaintReducer from './slices/complaintSlice';
import chatReducer from './slices/chatSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    complaint: complaintReducer,
    chat: chatReducer,
    ui: uiReducer,
  },
});
