import React, { useEffect, useRef } from 'react';

export default function ChatMessageList({ messages = [], isLoading = false, suggestions = [], onSelectSuggestion }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, suggestions]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      marginTop: '12px',
    }}>
      {messages.map((m, idx) => {
        const isUser = m.role === 'user';
        return (
          <div
            key={idx}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: isUser ? 'flex-end' : 'flex-start',
            }}
          >
            <div style={{
              fontSize: '11px',
              color: 'var(--text-muted)',
              marginBottom: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}>
              {!isUser && <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />}
              {isUser ? 'You' : 'Copilot'}
            </div>
            <div
              style={{
                maxWidth: '85%',
                padding: '10px 14px',
                borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                background: isUser ? 'var(--accent-dim)' : 'var(--bg-surface)',
                border: isUser ? '1px solid rgba(56,189,248,0.3)' : '1px solid var(--border-md)',
                color: isUser ? 'var(--accent)' : 'var(--text-primary)',
                fontSize: '13px',
                lineHeight: '1.5',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {m.content}
            </div>
          </div>
        );
      })}

      {isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Copilot</div>
          <div style={{
            padding: '8px 14px',
            borderRadius: '12px 12px 12px 2px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-md)',
            color: 'var(--text-muted)',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span style={{ animation: 'pulse-dot 1s infinite' }}>💭</span> Thinking...
          </div>
        </div>
      )}

      {/* Quick Reply Suggestions */}
      {!isLoading && suggestions && suggestions.length > 0 && (
        <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-label)', fontWeight: 600 }}>
            Suggested questions:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {suggestions.map((sug, i) => (
              <button
                key={i}
                onClick={() => onSelectSuggestion && onSelectSuggestion(sug)}
                style={{
                  background: 'rgba(56, 189, 248, 0.08)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  borderRadius: '16px',
                  color: 'var(--accent)',
                  padding: '5px 12px',
                  fontSize: '11.5px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background 0.2s, border-color 0.2s',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = 'rgba(56, 189, 248, 0.18)';
                  e.currentTarget.style.borderColor = 'var(--accent)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = 'rgba(56, 189, 248, 0.08)';
                  e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.25)';
                }}
              >
                💡 {sug}
              </button>
            ))}
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
