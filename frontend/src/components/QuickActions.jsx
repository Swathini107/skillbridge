import React from 'react';
import { useNavigate } from 'react-router-dom';
import { BookmarkPlus, FileSearch, Mic2, Mic, ArrowRight } from 'lucide-react';

const actions = [
  {
    title: 'Save a Job',
    description: 'Add new job postings to track application deadlines and status.',
    targetPath: '/applications',
    icon: BookmarkPlus,
    iconBg: '#eef2ff',
    iconColor: '#4f46e5',
    ctaText: 'Open Application Tracker',
    isAddJob: true
  },
  {
    title: 'Analyze a Job Description',
    description: 'Extract must-have technical skills, keywords, and qualifications.',
    targetPath: '/job-analyzer',
    icon: FileSearch,
    iconBg: '#f0f9ff',
    iconColor: '#0284c7',
    ctaText: 'Open Job Analyzer'
  },
  {
    title: 'Interview Memory Bank',
    description: 'Record and organize questions encountered in technical and HR rounds.',
    targetPath: '/questions',
    icon: Mic2,
    iconBg: '#faf5ff',
    iconColor: '#9333ea',
    ctaText: 'Open Question Bank'
  },
  {
    title: 'Mock Interview Studio',
    description: 'Practice role-specific interview rounds with timer and structured self-review.',
    targetPath: '/practice',
    icon: Mic,
    iconBg: '#eff6ff',
    iconColor: '#2563eb',
    ctaText: 'Start Mock Interview'
  }
];

export default function QuickActions({ onOpenAddJob }) {
  const navigate = useNavigate();

  const handleAction = (act) => {
    if (act.isAddJob && onOpenAddJob) {
      onOpenAddJob();
    } else {
      navigate(act.targetPath);
    }
  };

  return (
    <section>
      <div className="section-header">
        <h2 className="section-title">Quick Actions</h2>
        <p className="section-desc">
          Common student workflows to jumpstart your career preparation.
        </p>
      </div>

      <div className="quick-actions-grid">
        {actions.map((act) => {
          const Icon = act.icon;
          return (
            <div
              key={act.title}
              className="quick-action-card"
              onClick={() => handleAction(act)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleAction(act);
                }
              }}
            >
              <div
                className="quick-action-icon"
                style={{ backgroundColor: act.iconBg, color: act.iconColor }}
              >
                <Icon size={22} />
              </div>
              <div className="quick-action-body">
                <h3>{act.title}</h3>
                <p>{act.description}</p>
                <span className="quick-action-link">
                  {act.ctaText} <ArrowRight size={14} />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
