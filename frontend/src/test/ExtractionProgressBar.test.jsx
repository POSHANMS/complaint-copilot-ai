/**
 * Tests for ExtractionProgressBar component.
 * Renders from Redux store state — uses a mock store provider.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import ExtractionProgressBar from '../components/AICopilot/ExtractionProgressBar';

// Minimal Redux store factory for testing
function makeStore(uiState) {
  return configureStore({
    reducer: {
      ui: () => uiState,
    },
  });
}

describe('ExtractionProgressBar', () => {
  it('does NOT render when isExtracting=false and progress is 0', () => {
    const store = makeStore({ isExtracting: false, extractionProgress: 0, extractionStatusText: '' });
    const { container } = render(
      <Provider store={store}>
        <ExtractionProgressBar />
      </Provider>
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders progress bar when isExtracting=true', () => {
    const store = makeStore({
      isExtracting: true,
      extractionProgress: 42,
      extractionStatusText: 'Running extract_entities node (LLM)...',
    });
    render(
      <Provider store={store}>
        <ExtractionProgressBar />
      </Provider>
    );
    expect(screen.getByText('42%')).toBeInTheDocument();
    expect(screen.getByText('Running extract_entities node (LLM)...')).toBeInTheDocument();
  });

  it('renders progress bar when extractionProgress is 100 (even if not extracting)', () => {
    const store = makeStore({
      isExtracting: false,
      extractionProgress: 100,
      extractionStatusText: 'Extraction complete!',
    });
    render(
      <Provider store={store}>
        <ExtractionProgressBar />
      </Provider>
    );
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('Extraction complete!')).toBeInTheDocument();
  });

  it('shows default status text when extractionStatusText is empty', () => {
    const store = makeStore({
      isExtracting: true,
      extractionProgress: 28,
      extractionStatusText: '',
    });
    render(
      <Provider store={store}>
        <ExtractionProgressBar />
      </Provider>
    );
    // Should render fallback text from component
    expect(screen.getByText('Analyzing document content...')).toBeInTheDocument();
  });

  it('renders progress fill bar with correct width style', () => {
    const store = makeStore({
      isExtracting: true,
      extractionProgress: 75,
      extractionStatusText: 'Processing...',
    });
    const { container } = render(
      <Provider store={store}>
        <ExtractionProgressBar />
      </Provider>
    );
    const fill = container.querySelector('.progress-fill');
    expect(fill).toBeInTheDocument();
    expect(fill.style.width).toBe('75%');
  });

  it('renders correct node names for each pipeline stage', () => {
    const nodes = [
      { text: 'Running ingest_document node...', pct: 14 },
      { text: 'Running extract_entities node (LLM)...', pct: 28 },
      { text: 'Running classify_severity_risk node (LLM)...', pct: 57 },
    ];
    nodes.forEach(({ text, pct }) => {
      const store = makeStore({
        isExtracting: true,
        extractionProgress: pct,
        extractionStatusText: text,
      });
      const { unmount } = render(
        <Provider store={store}>
          <ExtractionProgressBar />
        </Provider>
      );
      expect(screen.getByText(text)).toBeInTheDocument();
      unmount();
    });
  });
});
