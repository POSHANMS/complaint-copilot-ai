import React from 'react';

export default function DuplicateWarningBanner({ isDuplicate, duplicateMatchId }) {
  if (!isDuplicate) return null;

  const shortId = duplicateMatchId ? duplicateMatchId.split('-')[0] : 'unknown';

  return (
    <div style={{
      background: 'rgba(245, 158, 11, 0.08)',
      border: '1px solid rgba(245, 158, 11, 0.4)',
      borderLeft: '4px solid var(--major)',
      borderRadius: '8px',
      padding: '12px 16px',
      marginTop: '12px',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px'
    }}>
      <span style={{ fontSize: '18px', flexShrink: 0 }}>⚠️</span>
      <div>
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--major)', marginBottom: '3px' }}>
          Potential Duplicate Complaint Detected
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
          This complaint shares the same batch/lot number as an existing record in the QMS database.
          Matched complaint ID: <code style={{ background: 'var(--bg-surface)', padding: '1px 5px', borderRadius: '3px', fontSize: '11px' }}>{shortId}...</code>
          &nbsp;— Please review the original complaint before logging a new record.
        </div>
      </div>
    </div>
  );
}
