import React from 'react';

export default function SummaryCard({
  title,
  value = 0,
  icon: Icon,
  iconBg = '#eef2ff',
  iconColor = '#4f46e5',
  tagText = 'Day 1 Initialized',
  subtext = '0 records recorded'
}) {
  return (
    <div className="summary-card">
      <div className="summary-card-header">
        <span className="summary-card-title">{title}</span>
        <div
          className="summary-card-icon"
          style={{ backgroundColor: iconBg, color: iconColor }}
        >
          {Icon && <Icon size={20} />}
        </div>
      </div>
      <div className="summary-card-value">{value}</div>
      <div className="summary-card-footer">
        <span className="sample-tag">{tagText}</span>
        <span className="sample-trend">{subtext}</span>
      </div>
    </div>
  );
}
