import React from 'react';
import { useSelector } from 'react-redux';

export default function ExtractionProgressBar() {
  const { isExtracting, extractionProgress, extractionStatusText } = useSelector(state => state.ui);

  if (!isExtracting && extractionProgress !== 100) return null;

  return (
    <div className="progress-wrapper">
      <div className="progress-header">
        <span>{extractionStatusText || 'Analyzing document content...'}</span>
        <span>{extractionProgress}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${extractionProgress}%` }} />
      </div>
    </div>
  );
}
