import React from 'react';

export default function CompletenessChecklist({ score = 100, missingFields = [] }) {
  return (
    <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
      <h4>Completeness: {score}%</h4>
      {missingFields.length > 0 && <p style={{ color: 'var(--severity-major)' }}>Missing: {missingFields.join(', ')}</p>}
    </div>
  );
}
