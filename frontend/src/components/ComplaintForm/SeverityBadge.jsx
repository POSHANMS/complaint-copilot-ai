import React from 'react';

export default function SeverityBadge({ severity = 'Minor' }) {
  const colors = {
    Critical: 'var(--severity-critical)',
    Major: 'var(--severity-major)',
    Minor: 'var(--severity-minor)',
  };
  return (
    <span style={{
      backgroundColor: colors[severity] || colors.Minor,
      color: '#fff',
      padding: '4px 10px',
      borderRadius: '12px',
      fontSize: '0.8rem',
      fontWeight: 600
    }}>
      {severity}
    </span>
  );
}
