import React from 'react';
import { useSelector } from 'react-redux';
import UploadDropzone from './UploadDropzone';
import ExtractionProgressBar from './ExtractionProgressBar';

import RiskScoreCard from '../RiskPanel/RiskScoreCard';
import CompletenessChecklist from '../RiskPanel/CompletenessChecklist';

export default function AICopilotPanel() {
  const { aiSummary, severity, priority, riskScore, riskReasoning, completenessScore, missingFields, extractionError } = useSelector(state => state.complaint);
  const { isExtracting } = useSelector(state => state.ui);

  return (
    <div className="copilot-panel">
      <div className="copilot-header">
        <div className="copilot-title">
          <span>✨</span> AI Complaint Intake Assistant
        </div>
        <div className="copilot-sub">
          Upload document or paste text to extract structured QMS fields
        </div>
      </div>

      <div className="copilot-body">
        <UploadDropzone />
        <ExtractionProgressBar />

        {extractionError && (
          <div className="error-msg">
            ⚠️ {extractionError}
          </div>
        )}

        {aiSummary && !isExtracting && (
          <>
            <div className="chat-bubble-container">
              <div className="chat-bubble-meta">
                <span className="ai-dot"></span>
                <strong>Complaint Copilot AI</strong> • Executive Summary
              </div>
              <div className="chat-bubble">
                {aiSummary}
              </div>
            </div>

            <RiskScoreCard
              severity={severity?.value}
              priority={priority?.value}
              riskScore={riskScore}
              riskReasoning={riskReasoning}
            />

            <CompletenessChecklist
              completenessScore={completenessScore}
              missingFields={missingFields}
            />
          </>
        )}

        {!aiSummary && !isExtracting && !extractionError && (
          <div className="idle-hint">
            <div className="idle-hint-icon">🤖</div>
            <div>Ready for document intake</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
              Upload a PDF/DOCX or paste text to begin automated extraction
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
