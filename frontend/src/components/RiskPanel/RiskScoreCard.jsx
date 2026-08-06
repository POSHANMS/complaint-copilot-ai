import React from 'react';

export default function RiskScoreCard({ severity, priority, riskScore, riskReasoning }) {
  if (!severity && !riskReasoning) return null;

  const sevLower = (severity || 'minor').toLowerCase();
  let badgeColor = 'var(--minor)';
  let borderColor = 'var(--border-md)';
  
  if (sevLower.includes('critical')) {
    badgeColor = 'var(--critical)';
    borderColor = 'var(--critical)';
  } else if (sevLower.includes('major')) {
    badgeColor = 'var(--major)';
    borderColor = 'var(--major)';
  }

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-md)',
      borderLeft: `4px solid ${borderColor}`,
      borderRadius: '8px',
      padding: '14px 16px',
      marginTop: '12px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>⚠️</span> AI Risk Assessment
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{
            background: badgeColor,
            color: '#fff',
            fontSize: '11px',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '4px',
            textTransform: 'uppercase'
          }}>
            {severity}
          </span>
          <span style={{
            background: 'var(--bg-input)',
            border: '1px solid var(--border-md)',
            color: 'var(--text-secondary)',
            fontSize: '11px',
            fontWeight: 600,
            padding: '2px 8px',
            borderRadius: '4px'
          }}>
            Priority: {priority}
          </span>
          {riskScore > 0 && (
            <span style={{ fontSize: '11px', color: 'var(--accent)', fontWeight: 600 }}>
              {riskScore}/100 Risk
            </span>
          )}
        </div>
      </div>

      <div style={{ fontSize: '12.5px', color: 'var(--text-primary)', lineHeight: '1.55', background: 'var(--bg-panel)', padding: '10px 12px', borderRadius: '6px', border: '1px solid var(--border)' }}>
        <strong>Justification: </strong>{riskReasoning}
      </div>
    </div>
  );
}
