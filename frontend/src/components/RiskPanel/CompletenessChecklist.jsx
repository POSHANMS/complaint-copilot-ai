import React from 'react';

export default function CompletenessChecklist({ completenessScore = 100, missingFields = [] }) {
  if (completenessScore === 0 && missingFields.length === 0) return null;

  const isComplete = completenessScore >= 90 && missingFields.length === 0;

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-md)',
      borderLeft: `4px solid ${isComplete ? 'var(--success)' : 'var(--major)'}`,
      borderRadius: '8px',
      padding: '14px 16px',
      marginTop: '12px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>{isComplete ? '✅' : '📊'}</span> Complaint Completeness Check
        </div>
        <div style={{
          background: isComplete ? 'rgba(34, 197, 94, 0.15)' : 'rgba(245, 158, 11, 0.15)',
          color: isComplete ? 'var(--success)' : 'var(--major)',
          fontSize: '11px',
          fontWeight: 700,
          padding: '2px 8px',
          borderRadius: '4px'
        }}>
          {completenessScore}% Complete
        </div>
      </div>

      <div style={{ width: '100%', height: '5px', background: 'var(--bg-panel)', borderRadius: '3px', overflow: 'hidden', marginBottom: '8px' }}>
        <div style={{
          width: `${completenessScore}%`,
          height: '100%',
          background: isComplete ? 'var(--success)' : 'var(--major)',
          transition: 'width 0.4s ease'
        }} />
      </div>

      {missingFields.length > 0 ? (
        <div style={{ fontSize: '12px', color: 'var(--major)', background: 'var(--bg-panel)', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border)' }}>
          <strong>⚠️ Incomplete Data Warning:</strong> Missing required fields: {missingFields.map(f => f.replace(/_/g, ' ')).join(', ')}.
        </div>
      ) : (
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          All 11 mandatory QMS intake fields successfully identified and extracted.
        </div>
      )}
    </div>
  );
}
