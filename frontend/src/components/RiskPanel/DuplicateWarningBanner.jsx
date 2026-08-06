import React from 'react';

export default function DuplicateWarningBanner({ isDuplicate, duplicateMatchId }) {
  if (!isDuplicate) return null;
  return (
    <div style={{ padding: '0.8rem', background: '#7f1d1d', color: '#fca5a5', borderRadius: '6px', margin: '0.5rem 0' }}>
      ⚠️ Warning: Potential duplicate complaint detected!
    </div>
  );
}
