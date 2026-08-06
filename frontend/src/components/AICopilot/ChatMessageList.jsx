import React from 'react';

export default function ChatMessageList({ messages = [] }) {
  return (
    <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {messages.map((m, idx) => (
        <div key={idx} style={{ padding: '8px 12px', borderRadius: '6px', background: m.role === 'user' ? 'var(--accent-hover)' : 'var(--bg-surface)' }}>
          <strong>{m.role}: </strong>{m.content}
        </div>
      ))}
    </div>
  );
}
