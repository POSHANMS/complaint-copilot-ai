import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  extractedFields: {
    complaint_source: '',
    customer_name: '',
    product_name: '',
    product_strength_grade: '',
    batch_lot_number: '',
    manufacturing_date: '',
    expiry_date: '',
    quantity_affected: '',
    complaint_type: '',
    complaint_date: '',
    detailed_description: '',
  },
  fieldStatus: {}, // 'idle' | 'loading' | 'extracted'
  completenessScore: 0,
  missingFields: [],
  severity: null,
  priority: null,
  riskScore: 0,
  riskReasoning: '',
  isDuplicate: false,
  duplicateMatchId: null,
  capaRecommendation: '',
  aiSummary: '',
  status: 'Pending Triage',
};

const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    setField: (state, action) => {
      const { field, value, status } = action.payload;
      state.extractedFields[field] = value;
      if (status) {
        state.fieldStatus[field] = status;
      }
    },
    resetForm: () => initialState,
  },
});

export const { setField, resetForm } = complaintSlice.actions;
export default complaintSlice.reducer;
