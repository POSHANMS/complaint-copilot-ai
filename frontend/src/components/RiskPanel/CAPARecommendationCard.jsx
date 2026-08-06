import React from 'react';

export default function CAPARecommendationCard({ recommendation }) {
  if (!recommendation) return null;

  // Extract [Category] tag if present
  const match = recommendation.match(/^\[(.*?)\]\s*(.*)$/s);
  const category = match ? match[1] : 'Material';
  const text = match ? match[2] : recommendation;

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-md)',
      borderLeft: '4px solid var(--accent)',
      borderRadius: '8px',
      padding: '14px 16px',
      marginTop: '12px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>🛠️</span> Recommended CAPA & 5M Root Cause
        </div>
        <div style={{
          background: 'var(--accent-dim)',
          color: 'var(--accent)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          fontSize: '11px',
          fontWeight: 700,
          padding: '2px 8px',
          borderRadius: '4px',
          textTransform: 'uppercase'
        }}>
          5M: {category}
        </div>
      </div>

      <div style={{ fontSize: '12.5px', color: 'var(--text-primary)', lineHeight: '1.6', background: 'var(--bg-panel)', padding: '10px 12px', borderRadius: '6px', border: '1px solid var(--border)' }}>
        {text}
      </div>
    </div>
  );
}
