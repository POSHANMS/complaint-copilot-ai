import React from 'react';

export default function FieldGroup({ title, children }) {
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--accent-primary)' }}>{title}</h3>
      {children}
    </div>
  );
}
