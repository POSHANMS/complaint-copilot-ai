import React from 'react';

export default function RiskScoreCard({ riskScore, reasoning }) {
  return (
    <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px', borderLeft: '4px solid var(--severity-major)' }}>
      <h4>AI Risk Assessment</h4>
      <p>{reasoning || 'Awaiting risk classification node...'}</p>
    </div>
  );
}
