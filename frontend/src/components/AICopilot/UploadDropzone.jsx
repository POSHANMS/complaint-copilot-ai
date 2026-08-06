import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { useExtractionStream } from '../../hooks/useExtractionStream';

export default function UploadDropzone() {
  const { isExtracting } = useSelector(state => state.ui);
  const { startExtraction } = useExtractionStream();
  
  const [selectedFile, setSelectedFile] = useState(null);
  const [rawText, setRawText] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = () => {
    if (!selectedFile && !rawText.trim()) return;
    startExtraction({ file: selectedFile, rawText });
  };

  return (
    <div className="copilot-upload-section">
      <div
        className={`dropzone ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleFileDrop}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <div className="dropzone-icon">📄</div>
        <div className="dropzone-title">Upload Complaint Document</div>
        <div className="dropzone-sub">Drag & drop PDF, DOCX, or TXT file here, or click to browse</div>
        {selectedFile && (
          <div className="file-selected" onClick={(e) => e.stopPropagation()}>
            📎 Selected: <strong>{selectedFile.name}</strong> ({Math.round(selectedFile.size / 1024)} KB)
          </div>
        )}
      </div>

      <div className="dropzone-or">OR PASTE COMPLAINT TEXT</div>

      <textarea
        className="paste-textarea"
        placeholder="Paste customer email, phone transcript, or complaint text here..."
        value={rawText}
        onChange={(e) => setRawText(e.target.value)}
        disabled={isExtracting}
      />

      <button
        className="btn-extract"
        onClick={handleSubmit}
        disabled={isExtracting || (!selectedFile && !rawText.trim())}
      >
        {isExtracting ? 'Extracting with AI...' : '⚡ Extract Complaint Fields'}
      </button>
    </div>
  );
}
