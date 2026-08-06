import React, { useState } from 'react';

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
      <input 
        type="text" 
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Run extraction to chat..." : "Ask a question about this complaint..."}
        disabled={disabled}
        style={{
          flex: 1,
          padding: '10px 14px',
          background: 'var(--bg-input)',
          border: '1px solid var(--border-md)',
          color: 'var(--text-primary)',
          borderRadius: '6px',
          fontSize: '12.5px',
          outline: 'none',
          opacity: disabled ? 0.5 : 1,
        }}
      />
      <button 
        type="submit"
        disabled={disabled || !text.trim()}
        style={{
          padding: '10px 16px',
          background: disabled || !text.trim() ? 'var(--border-md)' : 'var(--accent)',
          color: disabled || !text.trim() ? 'var(--text-muted)' : '#0b1120',
          border: 'none',
          borderRadius: '6px',
          fontWeight: 700,
          fontSize: '12.5px',
          cursor: disabled || !text.trim() ? 'not-allowed' : 'pointer',
          transition: 'background 0.2s',
        }}
      >
        Send
      </button>
    </form>
  );
}
