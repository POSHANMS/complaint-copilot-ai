import React from 'react';
import './styles/globals.css';

function App() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: 'var(--bg-primary)',
      color: 'var(--text-primary)',
      fontFamily: 'var(--font-family)',
      padding: '2rem'
    }}>
      <div style={{
        padding: '2.5rem 3.5rem',
        borderRadius: '12px',
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        textAlign: 'center',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)'
      }}>
        <h1 style={{
          fontSize: '2.25rem',
          fontWeight: 700,
          margin: 0,
          background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Complaint Copilot AI
        </h1>
        <p style={{
          marginTop: '1rem',
          color: 'var(--text-secondary)',
          fontSize: '1.05rem'
        }}>
          Pharma Quality Management System Intake Copilot
        </p>
        <div style={{
          marginTop: '1.5rem',
          padding: '0.5rem 1rem',
          borderRadius: '20px',
          backgroundColor: 'var(--bg-surface)',
          display: 'inline-block',
          fontSize: '0.85rem',
          color: 'var(--accent-primary)',
          fontWeight: 500
        }}>
          Step 1: Scaffolding Complete
        </div>
      </div>
    </div>
  );
}

export default App;
