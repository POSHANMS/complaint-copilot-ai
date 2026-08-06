import React from 'react';

export default function SeverityBadge({ severity, priority }) {
  const getSeverityClass = (val) => {
    if (!val) return 'minor';
    const lower = val.toLowerCase();
    if (lower.includes('critical')) return 'critical';
    if (lower.includes('major')) return 'major';
    return 'minor';
  };

  return (
    <div style={{ display: 'flex', gap: '10px' }}>
      <div className="field-row" style={{ flex: 1 }}>
        <label className="field-label">Initial Severity</label>
        <div className="field-value empty">
          {severity?.value ? (
            <span style={{
              background: `var(--severity-${getSeverityClass(severity.value)})`,
              color: '#fff',
              padding: '2px 8px',
              borderRadius: '4px',
              fontWeight: 600,
              fontSize: '11px'
            }}>
              {severity.value}
            </span>
          ) : 'Awaiting AI extraction...'}
        </div>
      </div>

      <div className="field-row" style={{ flex: 1 }}>
        <label className="field-label">Priority</label>
        <div className="field-value empty">
          {priority?.value || 'Awaiting AI extraction...'}
        </div>
      </div>
    </div>
  );
}
