/**
 * Tests for complaintSlice Redux reducers.
 * Tests processNodeStreamUpdate — the real-time SSE stream handler.
 * Pure reducer tests, no React rendering needed.
 */
import { describe, it, expect } from 'vitest';
import reducer, {
  processNodeStreamUpdate,
  setAllFieldsLoading,
  setAllFieldsEmpty,
  setSingleField,
  resetComplaintState,
} from '../store/slices/complaintSlice';

const FIELDS = [
  'complaint_source', 'customer_name', 'product_name', 'product_strength_grade',
  'batch_lot_number', 'manufacturing_date', 'expiry_date', 'quantity_affected',
  'complaint_type', 'complaint_date', 'detailed_description',
];

function emptyState() {
  return reducer(undefined, { type: '@@INIT' });
}

describe('complaintSlice — processNodeStreamUpdate', () => {
  it('extract_entities node: populates fields from partial_state', () => {
    const initial = emptyState();
    const action = processNodeStreamUpdate({
      node: 'extract_entities',
      partial_state: {
        extracted_fields: {
          product_name: 'Atorvastatin 40mg Tablets',
          batch_lot_number: 'ATR-2024-B0421',
          complaint_source: 'Retail Pharmacy',
        },
      },
    });
    const state = reducer(initial, action);

    expect(state.fields.product_name.value).toBe('Atorvastatin 40mg Tablets');
    expect(state.fields.product_name.status).toBe('filled');
    expect(state.fields.batch_lot_number.value).toBe('ATR-2024-B0421');
    // Fields not in partial_state remain as-is
    expect(state.fields.customer_name.status).toBe('empty');
  });

  it('validate_completeness node: updates completeness score and missing fields', () => {
    const initial = emptyState();
    const action = processNodeStreamUpdate({
      node: 'validate_completeness',
      partial_state: {
        completeness_score: 72.7,
        missing_fields: ['manufacturing_date', 'expiry_date', 'quantity_affected'],
      },
    });
    const state = reducer(initial, action);

    expect(state.completenessScore).toBe(72.7);
    expect(state.missingFields).toEqual(['manufacturing_date', 'expiry_date', 'quantity_affected']);
  });

  it('classify_severity_risk node: updates severity, priority, risk_score, risk_reasoning', () => {
    const initial = emptyState();
    const action = processNodeStreamUpdate({
      node: 'classify_severity_risk',
      partial_state: {
        severity: 'Critical',
        priority: 'High',
        risk_score: 90.0,
        risk_reasoning: 'Seal integrity failure confirmed. No hospitalization occurred.',
      },
    });
    const state = reducer(initial, action);

    expect(state.severity).toEqual({ value: 'Critical', status: 'filled' });
    expect(state.priority).toEqual({ value: 'High', status: 'filled' });
    expect(state.riskScore).toBe(90.0);
    expect(state.riskReasoning).toBe('Seal integrity failure confirmed. No hospitalization occurred.');
  });

  it('detect_duplicate node: sets isDuplicate and duplicateMatchId', () => {
    const initial = emptyState();
    const action = processNodeStreamUpdate({
      node: 'detect_duplicate',
      partial_state: {
        is_duplicate: true,
        duplicate_match_id: 'canonical-root-id-abc',
      },
    });
    const state = reducer(initial, action);

    expect(state.isDuplicate).toBe(true);
    expect(state.duplicateMatchId).toBe('canonical-root-id-abc');
  });

  it('detect_duplicate node: handles non-duplicate correctly', () => {
    const initial = emptyState();
    const action = processNodeStreamUpdate({
      node: 'detect_duplicate',
      partial_state: {
        is_duplicate: false,
        duplicate_match_id: null,
      },
    });
    const state = reducer(initial, action);

    expect(state.isDuplicate).toBe(false);
    expect(state.duplicateMatchId).toBeNull();
  });

  it('recommend_capa node: sets capaRecommendation', () => {
    const initial = emptyState();
    const action = processNodeStreamUpdate({
      node: 'recommend_capa',
      partial_state: {
        capa_recommendation: '[Machine] Inspect and recalibrate blister sealing machine.',
      },
    });
    const state = reducer(initial, action);

    expect(state.capaRecommendation).toBe('[Machine] Inspect and recalibrate blister sealing machine.');
  });

  it('generate_summary node: sets aiSummary', () => {
    const initial = emptyState();
    const action = processNodeStreamUpdate({
      node: 'generate_summary',
      partial_state: {
        summary: 'A Critical complaint about Atorvastatin 40mg batch ATR-2024-B0421.',
      },
    });
    const state = reducer(initial, action);

    expect(state.aiSummary).toBe('A Critical complaint about Atorvastatin 40mg batch ATR-2024-B0421.');
  });

  it('END node: sets complaintId and updates final summary', () => {
    const initial = emptyState();
    const action = processNodeStreamUpdate({
      node: 'END',
      complaint_id: 'final-uuid-abc123',
      final_state: { summary: 'Final executive summary text.' },
    });
    const state = reducer(initial, action);

    expect(state.complaintId).toBe('final-uuid-abc123');
    expect(state.aiSummary).toBe('Final executive summary text.');
  });

  it('unknown node: does not modify state unexpectedly', () => {
    const initial = emptyState();
    const action = processNodeStreamUpdate({
      node: 'unknown_future_node',
      partial_state: { foo: 'bar' },
    });
    const state = reducer(initial, action);

    // State should be unchanged
    expect(state.isDuplicate).toBe(false);
    expect(state.aiSummary).toBe('');
  });
});

describe('complaintSlice — field reducers', () => {
  it('setAllFieldsLoading: sets all fields to loading status', () => {
    const initial = emptyState();
    const state = reducer(initial, setAllFieldsLoading());

    FIELDS.forEach(field => {
      expect(state.fields[field].status).toBe('loading');
    });
    expect(state.aiSummary).toBe('');
    expect(state.extractionError).toBeNull();
  });

  it('setAllFieldsEmpty: sets all fields to empty status', () => {
    const loadingState = reducer(emptyState(), setAllFieldsLoading());
    const state = reducer(loadingState, setAllFieldsEmpty());

    FIELDS.forEach(field => {
      expect(state.fields[field].status).toBe('empty');
    });
  });

  it('setSingleField: updates a specific field value and status', () => {
    const initial = emptyState();
    const state = reducer(initial, setSingleField({
      field: 'product_name',
      value: 'Atorvastatin 40mg Tablets',
      status: 'filled',
    }));

    expect(state.fields.product_name.value).toBe('Atorvastatin 40mg Tablets');
    expect(state.fields.product_name.status).toBe('filled');
    // Other fields should remain untouched
    expect(state.fields.batch_lot_number.status).toBe('empty');
  });

  it('setSingleField: handles null value gracefully (sets to empty string)', () => {
    const initial = emptyState();
    const state = reducer(initial, setSingleField({
      field: 'manufacturing_date',
      value: null,
      status: 'filled',
    }));

    expect(state.fields.manufacturing_date.value).toBe('');
  });

  it('resetComplaintState: returns full initial state', () => {
    // Put some data in first
    let state = emptyState();
    state = reducer(state, setSingleField({ field: 'product_name', value: 'Test', status: 'filled' }));
    state = reducer(state, processNodeStreamUpdate({
      node: 'classify_severity_risk',
      partial_state: { severity: 'Critical', priority: 'High', risk_score: 90, risk_reasoning: 'test' },
    }));

    // Reset
    const resetted = reducer(state, resetComplaintState());
    expect(resetted.complaintId).toBeNull();
    expect(resetted.aiSummary).toBe('');
    expect(resetted.fields.product_name.value).toBe('');
    expect(resetted.severity.value).toBeNull();
  });
});
