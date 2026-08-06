import React from 'react';

export default function Button({ children, onClick, variant = 'primary' }) {
  return (
    <button 
      onClick={onClick}
      style={{
        padding: '8px 16px',
        backgroundColor: variant === 'primary' ? 'var(--accent-primary)' : 'var(--bg-surface)',
        color: '#fff',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
        fontWeight: 500
      }}
    >
      {children}
    </button>
  );
}
