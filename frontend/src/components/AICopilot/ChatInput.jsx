import React from 'react';

export default function ChatInput({ onSend }) {
  return (
    <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
      <input 
        type="text" 
        placeholder="Ask Complaint Copilot..." 
        style={{ flex: 1, padding: '8px 12px', background: 'var(--bg-surface)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '4px' }}
      />
      <button style={{ padding: '8px 16px', background: 'var(--accent-primary)', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
        Send
      </button>
    </div>
  );
}
