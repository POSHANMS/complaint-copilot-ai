import React from 'react';

export default function FieldGroup({ title, children }) {
  return (
    <div className="field-group">
      <div className="field-group-header">{title}</div>
      <div className="field-grid">{children}</div>
    </div>
  );
}
