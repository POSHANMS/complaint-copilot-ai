import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import UploadDropzone from './UploadDropzone';
import ExtractionProgressBar from './ExtractionProgressBar';
import ChatMessageList from './ChatMessageList';
import ChatInput from './ChatInput';

import RiskScoreCard from '../RiskPanel/RiskScoreCard';
import CompletenessChecklist from '../RiskPanel/CompletenessChecklist';
import CAPARecommendationCard from '../RiskPanel/CAPARecommendationCard';
import DuplicateWarningBanner from '../RiskPanel/DuplicateWarningBanner';

import { sendChatMessage } from '../../store/slices/chatSlice';

export default function AICopilotPanel() {
  const dispatch = useDispatch();
  const {
    complaintId,
    aiSummary,
    severity,
    priority,
    riskScore,
    riskReasoning,
    completenessScore,
    missingFields,
    capaRecommendation,
    isDuplicate,
    duplicateMatchId,
    extractionError
  } = useSelector(state => state.complaint);

  const { isExtracting } = useSelector(state => state.ui);
  const { messages, isLoading: isChatLoading, suggestions } = useSelector(state => state.chat);

  const handleSendMessage = (msgText) => {
    if (!complaintId) return;
    dispatch(sendChatMessage({ complaintId, message: msgText }));
  };

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

            <CAPARecommendationCard
              recommendation={capaRecommendation}
            />

            <DuplicateWarningBanner
              isDuplicate={isDuplicate}
              duplicateMatchId={duplicateMatchId}
            />

            {/* Interactive Chat Section */}
            <div style={{
              marginTop: '16px',
              paddingTop: '14px',
              borderTop: '1px solid var(--border-md)',
            }}>
              <div style={{
                fontSize: '12px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}>
                💬 Interactive Copilot Chat
              </div>

              <ChatMessageList
                messages={messages}
                isLoading={isChatLoading}
                suggestions={suggestions}
                onSelectSuggestion={handleSendMessage}
              />

              <ChatInput
                onSend={handleSendMessage}
                disabled={isExtracting || !complaintId || isChatLoading}
              />
            </div>
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
