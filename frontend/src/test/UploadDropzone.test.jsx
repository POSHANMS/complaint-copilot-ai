/**
 * Tests for UploadDropzone component.
 * Tests: render, file selection display, file accept attribute,
 * button disabled state, text area paste mode.
 *
 * Note: startExtraction (the actual upload + streaming) is mocked
 * since it hits the real API — we're testing the UI behaviour only.
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';

// Mock the hook that drives extraction so we don't need real Redux store with thunks
vi.mock('../hooks/useExtractionStream', () => ({
  useExtractionStream: () => ({
    startExtraction: vi.fn(),
  }),
}));

import UploadDropzone from '../components/AICopilot/UploadDropzone';

function makeStore(isExtracting = false) {
  return configureStore({
    reducer: {
      ui: () => ({ isExtracting }),
    },
  });
}

describe('UploadDropzone', () => {
  it('renders upload zone, text area, and extract button', () => {
    render(
      <Provider store={makeStore(false)}>
        <UploadDropzone />
      </Provider>
    );
    expect(screen.getByText(/Upload Complaint Document/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Paste customer email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Extract Complaint Fields/i })).toBeInTheDocument();
  });

  it('file input has correct accept attribute (.pdf, .docx, .txt)', () => {
    const { container } = render(
      <Provider store={makeStore(false)}>
        <UploadDropzone />
      </Provider>
    );
    const fileInput = container.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
    expect(fileInput).toHaveAttribute('accept', '.pdf,.docx,.txt');
  });

  it('extract button is disabled when no file or text is provided', () => {
    render(
      <Provider store={makeStore(false)}>
        <UploadDropzone />
      </Provider>
    );
    const button = screen.getByRole('button', { name: /Extract Complaint Fields/i });
    expect(button).toBeDisabled();
  });

  it('extract button becomes enabled after typing in text area', async () => {
    const user = userEvent.setup();
    render(
      <Provider store={makeStore(false)}>
        <UploadDropzone />
      </Provider>
    );

    const textarea = screen.getByPlaceholderText(/Paste customer email/i);
    await user.type(textarea, 'Atorvastatin packaging defect complaint.');

    const button = screen.getByRole('button', { name: /Extract Complaint Fields/i });
    expect(button).not.toBeDisabled();
  });

  it('shows selected file name after file is chosen', () => {
    const { container } = render(
      <Provider store={makeStore(false)}>
        <UploadDropzone />
      </Provider>
    );

    const fileInput = container.querySelector('input[type="file"]');
    const file = new File(['%PDF-1.4 content'], 'complaint.pdf', { type: 'application/pdf' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    expect(screen.getByText(/Selected:/i)).toBeInTheDocument();
    expect(screen.getByText(/complaint\.pdf/i)).toBeInTheDocument();
  });

  it('disables textarea and button during extraction (isExtracting=true)', () => {
    render(
      <Provider store={makeStore(true)}>
        <UploadDropzone />
      </Provider>
    );

    const textarea = screen.getByPlaceholderText(/Paste customer email/i);
    expect(textarea).toBeDisabled();

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('shows "Extracting with AI..." text on button during extraction', () => {
    render(
      <Provider store={makeStore(true)}>
        <UploadDropzone />
      </Provider>
    );
    expect(screen.getByText('Extracting with AI...')).toBeInTheDocument();
  });
});
