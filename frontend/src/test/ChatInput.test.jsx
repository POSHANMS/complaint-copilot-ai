/**
 * Tests for ChatInput component.
 * Verifies: Enter key submission, disabled state, text clearing after send.
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ChatInput from '../components/AICopilot/ChatInput';

describe('ChatInput', () => {
  let mockOnSend;

  beforeEach(() => {
    mockOnSend = vi.fn();
  });

  it('renders input and Send button', () => {
    render(<ChatInput onSend={mockOnSend} disabled={false} />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('calls onSend with trimmed text when Submit button clicked', async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={mockOnSend} disabled={false} />);

    const input = screen.getByRole('textbox');
    await user.type(input, '  What is the batch number?  ');
    await user.click(screen.getByRole('button', { name: /send/i }));

    expect(mockOnSend).toHaveBeenCalledOnce();
    expect(mockOnSend).toHaveBeenCalledWith('What is the batch number?');
  });

  it('calls onSend when Enter key is pressed (not Shift+Enter)', async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={mockOnSend} disabled={false} />);

    const input = screen.getByRole('textbox');
    await user.type(input, 'What is the risk level?');
    await user.keyboard('{Enter}');

    expect(mockOnSend).toHaveBeenCalledOnce();
    expect(mockOnSend).toHaveBeenCalledWith('What is the risk level?');
  });

  it('clears input text after successful submission', async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={mockOnSend} disabled={false} />);

    const input = screen.getByRole('textbox');
    await user.type(input, 'Some question');
    await user.keyboard('{Enter}');

    expect(input).toHaveValue('');
  });

  it('does NOT call onSend when input is empty or whitespace', async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={mockOnSend} disabled={false} />);

    // Click send with no text
    await user.click(screen.getByRole('button', { name: /send/i }));
    expect(mockOnSend).not.toHaveBeenCalled();

    // Type only spaces
    const input = screen.getByRole('textbox');
    await user.type(input, '   ');
    await user.keyboard('{Enter}');
    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('disables input and button when disabled=true', () => {
    render(<ChatInput onSend={mockOnSend} disabled={true} />);

    const input = screen.getByRole('textbox');
    const button = screen.getByRole('button', { name: /send/i });

    expect(input).toBeDisabled();
    expect(button).toBeDisabled();
  });

  it('shows disabled placeholder text when disabled=true', () => {
    render(<ChatInput onSend={mockOnSend} disabled={true} />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('placeholder', expect.stringMatching(/run extraction/i));
  });

  it('does NOT call onSend when disabled, even if Enter is pressed', async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={mockOnSend} disabled={true} />);

    // Typing into a disabled input is a no-op, but verify the guard works
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'Some text' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(mockOnSend).not.toHaveBeenCalled();
  });
});
