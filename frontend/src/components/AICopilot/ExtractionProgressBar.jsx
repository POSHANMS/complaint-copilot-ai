import React from 'react';

export default function ExtractionProgressBar({ progress = 0, statusText = '' }) {
  return (
    <div style={{ margin: '1rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
        <span>{statusText || 'Analyzing document...'}</span>
        <span>{progress}%</span>
      </div>
      <div style={{ height: '8px', background: 'var(--bg-surface)', borderRadius: '4px', marginTop: '4px', overflow: 'hidden' }}>
        <div style={{ width: `${progress}%`, height: '100%', background: 'var(--accent-primary)', transition: 'width 0.3s' }}></div>
      </div>
    </div>
  );
}
