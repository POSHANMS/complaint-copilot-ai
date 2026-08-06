import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../../api/client';

/** POST /api/complaints/{id}/chat */
export const sendChatMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ complaintId, message }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post(`/complaints/${complaintId}/chat`, { message });
      return { reply: response.data.reply, userMessage: message };
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message || 'Chat failed');
    }
  }
);

/** GET /api/complaints/{id}/chat/suggestions */
export const fetchSuggestions = createAsyncThunk(
  'chat/fetchSuggestions',
  async (complaintId, { rejectWithValue }) => {
    try {
      const response = await apiClient.get(`/complaints/${complaintId}/chat/suggestions`);
      return response.data.suggestions;
    } catch {
      return rejectWithValue([]);
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [],       // { role: 'user'|'assistant', content: string }
    isLoading: false,
    error: null,
    suggestions: [],
  },
  reducers: {
    clearChat: (state) => {
      state.messages = [];
      state.error = null;
      state.suggestions = [];
    },
  },
  extraReducers: (builder) => {
    builder
      // sendChatMessage
      .addCase(sendChatMessage.pending, (state, action) => {
        state.isLoading = true;
        state.error = null;
        // Optimistically add the user message
        state.messages.push({ role: 'user', content: action.meta.arg.message });
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.isLoading = false;
        state.messages.push({ role: 'assistant', content: action.payload.reply });
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload || 'Chat request failed';
        state.messages.push({ role: 'assistant', content: '⚠️ Could not reach the chat service. Please try again.' });
      })
      // fetchSuggestions
      .addCase(fetchSuggestions.fulfilled, (state, action) => {
        state.suggestions = action.payload;
      });
  },
});

export const { clearChat } = chatSlice.actions;
export default chatSlice.reducer;
