import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { apiExtractComplaint } from '../../api/client';
import { setExtracting, setProgress } from './uiSlice';

const FIELDS = [
  'complaint_source',
  'customer_name',
  'product_name',
  'product_strength_grade',
  'batch_lot_number',
  'manufacturing_date',
  'expiry_date',
  'quantity_affected',
  'complaint_type',
  'complaint_date',
  'detailed_description',
];

const createEmptyFieldsState = () => {
  const fields = {};
  FIELDS.forEach(f => {
    fields[f] = { value: '', status: 'empty' };
  });
  return fields;
};

const initialState = {
  fields: createEmptyFieldsState(),
  aiSummary: '',
  extractionError: null,
  // Future Step 4 nodes (stay empty/idle in Step 3)
  severity: { value: null, status: 'empty' },
  priority: { value: null, status: 'empty' },
  completenessScore: 0,
  missingFields: [],
  riskScore: 0,
  riskReasoning: '',
  isDuplicate: false,
  duplicateMatchId: null,
  capaRecommendation: '',
};

export const extractComplaintThunk = createAsyncThunk(
  'complaint/extract',
  async ({ file, rawText }, { dispatch }) => {
    try {
      dispatch(setExtracting(true));
      dispatch(setProgress({ progress: 15, statusText: 'Parsing document content...' }));

      // Set fields to loading state
      dispatch(setAllFieldsLoading());

      // Simulate step 1 progress
      await new Promise(r => setTimeout(r, 400));
      dispatch(setProgress({ progress: 45, statusText: 'Extracting pharmaceutical entities...' }));

      // Call API
      const result = await apiExtractComplaint({ file, rawText });

      dispatch(setProgress({ progress: 85, statusText: 'Generating executive summary...' }));
      await new Promise(r => setTimeout(r, 300));

      dispatch(setProgress({ progress: 100, statusText: 'Extraction complete!' }));
      dispatch(setExtracting(false));

      // Stagger field updates (150-300ms per field)
      const extracted = result.extracted_fields || {};
      const fieldsList = Object.keys(extracted);

      for (let i = 0; i < fieldsList.length; i++) {
        const fieldName = fieldsList[i];
        const fieldValue = extracted[fieldName];
        
        await new Promise(r => setTimeout(r, 180));
        dispatch(setSingleField({ field: fieldName, value: fieldValue, status: 'filled' }));
      }

      return result;
    } catch (err) {
      dispatch(setExtracting(false));
      dispatch(setAllFieldsEmpty());
      const errorMsg = err.response?.data?.detail || err.message || 'Extraction failed';
      throw new Error(errorMsg);
    }
  }
);

const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    setSingleField: (state, action) => {
      const { field, value, status } = action.payload;
      if (state.fields[field]) {
        state.fields[field] = {
          value: value ?? '',
          status: status || 'filled',
        };
      }
    },
    setAllFieldsLoading: (state) => {
      Object.keys(state.fields).forEach(key => {
        state.fields[key].status = 'loading';
      });
      state.aiSummary = '';
      state.extractionError = null;
    },
    setAllFieldsEmpty: (state) => {
      Object.keys(state.fields).forEach(key => {
        state.fields[key].status = 'empty';
      });
    },
    resetComplaintState: () => initialState,
  },
  extraReducers: (builder) => {
    builder
      .addCase(extractComplaintThunk.fulfilled, (state, action) => {
        state.aiSummary = action.payload.summary || '';
        state.extractionError = null;
      })
      .addCase(extractComplaintThunk.rejected, (state, action) => {
        state.extractionError = action.error.message;
      });
  },
});

export const {
  setSingleField,
  setAllFieldsLoading,
  setAllFieldsEmpty,
  resetComplaintState,
} = complaintSlice.actions;

export default complaintSlice.reducer;
