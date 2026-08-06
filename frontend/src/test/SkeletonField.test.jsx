/**
 * Tests for SkeletonField component.
 * Verifies: loading skeleton state, filled state, empty state with fallback text.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SkeletonField from '../components/ComplaintForm/SkeletonField';

describe('SkeletonField', () => {
  it('renders label text in all states', () => {
    render(<SkeletonField label="Batch / Lot Number" fieldData={{ status: 'empty', value: '' }} />);
    expect(screen.getByText('Batch / Lot Number')).toBeInTheDocument();
  });

  it('renders skeleton div when status is "loading"', () => {
    const { container } = render(
      <SkeletonField label="Product Name" fieldData={{ status: 'loading', value: '' }} />
    );
    // skeleton-field class is rendered for loading state
    const skeleton = container.querySelector('.skeleton-field');
    expect(skeleton).toBeInTheDocument();
  });

  it('does NOT render skeleton div when status is "filled"', () => {
    const { container } = render(
      <SkeletonField label="Product Name" fieldData={{ status: 'filled', value: 'Atorvastatin 40mg' }} />
    );
    const skeleton = container.querySelector('.skeleton-field');
    expect(skeleton).not.toBeInTheDocument();
  });

  it('renders actual field value when status is "filled"', () => {
    render(
      <SkeletonField label="Batch Number" fieldData={{ status: 'filled', value: 'ATR-2024-B0421' }} />
    );
    expect(screen.getByText('ATR-2024-B0421')).toBeInTheDocument();
  });

  it('shows fallback text "Awaiting AI extraction..." when status is "empty"', () => {
    render(
      <SkeletonField label="Expiry Date" fieldData={{ status: 'empty', value: '' }} />
    );
    expect(screen.getByText('Awaiting AI extraction...')).toBeInTheDocument();
  });

  it('shows fallback text when fieldData is undefined', () => {
    render(<SkeletonField label="Customer Name" fieldData={undefined} />);
    expect(screen.getByText('Awaiting AI extraction...')).toBeInTheDocument();
  });

  it('renders skeleton-field-tall class when isTall=true and loading', () => {
    const { container } = render(
      <SkeletonField
        label="Detailed Description"
        fieldData={{ status: 'loading', value: '' }}
        isTall={true}
      />
    );
    const skeleton = container.querySelector('.skeleton-field-tall');
    expect(skeleton).toBeInTheDocument();
  });

  it('renders field-value-tall class when isTall=true and filled', () => {
    const { container } = render(
      <SkeletonField
        label="Description"
        fieldData={{ status: 'filled', value: 'Long description text here.' }}
        isTall={true}
      />
    );
    const valueDiv = container.querySelector('.field-value-tall');
    expect(valueDiv).toBeInTheDocument();
    expect(valueDiv).toHaveTextContent('Long description text here.');
  });

  it('applies "empty" CSS class when value is empty string', () => {
    const { container } = render(
      <SkeletonField label="Quantity" fieldData={{ status: 'empty', value: '' }} />
    );
    const valueDiv = container.querySelector('.field-value.empty');
    expect(valueDiv).toBeInTheDocument();
  });
});
