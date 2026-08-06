import React from 'react';

export default function ProgressBar({ value = 0, max = 100 }) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--bg-surface)', borderRadius: '3px', overflow: 'hidden' }}>
      <div style={{ width: `${percentage}%`, height: '100%', backgroundColor: 'var(--accent-primary)', transition: 'width 0.3s' }}></div>
    </div>
  );
}
