import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  messages: [],
  isThinking: false,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    setThinking: (state, action) => {
      state.isThinking = action.payload;
    },
  },
});

export const { addMessage, setThinking } = chatSlice.actions;
export default chatSlice.reducer;
