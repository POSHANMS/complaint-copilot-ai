import React from 'react';

export default function SkeletonField({ label, fieldData, isTall = false }) {
  const status = fieldData?.status || 'empty';
  const value = fieldData?.value ?? '';

  return (
    <div className="field-row">
      <label className="field-label">{label}</label>
      {status === 'loading' ? (
        <div className={isTall ? 'skeleton-field-tall' : 'skeleton-field'} />
      ) : (
        <div className={`field-value ${isTall ? 'field-value-tall' : ''} ${!value ? 'empty' : ''}`}>
          {value || 'Awaiting AI extraction...'}
        </div>
      )}
    </div>
  );
}
