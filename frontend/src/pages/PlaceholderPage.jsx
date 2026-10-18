import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Compass
} from 'lucide-react';
import '../styles/placeholder.css';

export default function PlaceholderPage() {
  return (
    <div className="placeholder-page fade-in">
      <div className="placeholder-card">
        <div className="placeholder-icon-badge">
          <Compass size={32} />
        </div>

        <h1 className="placeholder-title" style={{ marginTop: '0.75rem' }}>Page Not Found (404)</h1>

        <p className="placeholder-desc">
          The requested page or resource could not be found. All core SkillBridge modules—Dashboard, Job Analyzer, Applications Tracker, Question Bank, and Mock Interview Studio—are available from the main workspace.
        </p>

        <div style={{ marginTop: '1.5rem' }}>
          <Link to="/" className="back-to-dashboard-btn">
            <ArrowLeft size={16} />
            <span>Return to Career Preparation Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
