import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  isExtracting: false,
  extractionProgress: 0,
  extractionStatusText: '',
  activeTab: 'form',
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setExtracting: (state, action) => {
      state.isExtracting = action.payload;
      if (action.payload) {
        state.extractionProgress = 0;
        state.extractionStatusText = 'Initializing extraction...';
      }
    },
    setProgress: (state, action) => {
      const { progress, statusText } = action.payload;
      state.extractionProgress = progress;
      if (statusText) state.extractionStatusText = statusText;
    },
    setActiveTab: (state, action) => {
      state.activeTab = action.payload;
    },
  },
});

export const { setExtracting, setProgress, setActiveTab } = uiSlice.actions;
export default uiSlice.reducer;
