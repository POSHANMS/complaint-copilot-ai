import React from 'react';

export default function CAPARecommendationCard({ recommendation }) {
  return (
    <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
      <h4>Draft CAPA Recommendation</h4>
      <p>{recommendation || 'Awaiting CAPA node...'}</p>
    </div>
  );
}
