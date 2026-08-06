import React from 'react';
import ComplaintForm from './components/ComplaintForm/ComplaintForm';
import AICopilotPanel from './components/AICopilot/AICopilotPanel';

export default function App() {
  return (
    <div className="app">
      {/* Top Navigation Header */}
      <header className="header">
        <div className="header-brand">
          <div className="header-icon">🛡️</div>
          <span>Complaint Copilot AI</span>
          <span className="header-badge">Pharma QMS</span>
        </div>

        <div className="header-meta">
          <div className="header-model-tag">
            <span className="model-dot"></span>
            <span>Groq llama-3.1-8b-instant</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Step 3 Scaffolding</span>
        </div>
      </header>

      {/* Main Split-Screen Layout */}
      <div className="main-layout">
        {/* Left Panel: Log Complaint Form */}
        <div className="panel-left">
          <ComplaintForm />
        </div>

        {/* Right Panel: AI Copilot Assistant */}
        <div className="panel-right">
          <AICopilotPanel />
        </div>
      </div>
    </div>
  );
}
