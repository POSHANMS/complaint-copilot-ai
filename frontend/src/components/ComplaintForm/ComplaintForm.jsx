import React from 'react';
import { useSelector } from 'react-redux';
import FieldGroup from './FieldGroup';
import SkeletonField from './SkeletonField';
import SeverityBadge from './SeverityBadge';

export default function ComplaintForm() {
  const { fields, severity, priority } = useSelector(state => state.complaint);

  return (
    <div>
      <div className="panel-title">
        <span className="panel-title-icon">📋</span>
        Log Complaint Form
      </div>

      {/* 1. Origin & Customer */}
      <FieldGroup title="1. Origin & Customer">
        <div className="field-grid-2">
          <SkeletonField label="Complaint Source" fieldData={fields.complaint_source} />
          <SkeletonField label="Customer / Facility Name" fieldData={fields.customer_name} />
        </div>
        <SkeletonField label="Complaint Date" fieldData={fields.complaint_date} />
      </FieldGroup>

      {/* 2. Product & Batch */}
      <FieldGroup title="2. Product & Batch Details">
        <div className="field-grid-2">
          <SkeletonField label="Product Name" fieldData={fields.product_name} />
          <SkeletonField label="Strength / Grade" fieldData={fields.product_strength_grade} />
        </div>
        <SkeletonField label="Batch / Lot Number" fieldData={fields.batch_lot_number} />
        <div className="field-grid-2">
          <SkeletonField label="Manufacturing Date" fieldData={fields.manufacturing_date} />
          <SkeletonField label="Expiry Date" fieldData={fields.expiry_date} />
        </div>
      </FieldGroup>

      {/* 3. Complaint Details */}
      <FieldGroup title="3. Complaint Details">
        <div className="field-grid-2">
          <SkeletonField label="Complaint Type" fieldData={fields.complaint_type} />
          <SkeletonField label="Quantity Affected" fieldData={fields.quantity_affected} />
        </div>
        <SkeletonField label="Detailed Description" fieldData={fields.detailed_description} isTall={true} />
      </FieldGroup>

      {/* 4. Initial Assessment */}
      <FieldGroup title="4. Initial Assessment (AI Triage)">
        <SeverityBadge severity={severity} priority={priority} />
      </FieldGroup>
    </div>
  );
}
