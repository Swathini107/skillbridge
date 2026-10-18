import React from 'react';
import {
  Briefcase,
  Target,
  MessageSquareCode,
  CheckCircle2,
  CalendarDays
} from 'lucide-react';

const pillars = [
  {
    badge: 'Module 2 & 6',
    badgeBg: '#eef2ff',
    badgeColor: '#4f46e5',
    title: 'Track Applications',
    description:
      'Organize your job search in a structured pipeline. Never miss follow-up deadlines, interview dates, or offer windows.',
    icon: Briefcase,
    features: [
      'Visual status tracking (Saved, Applied, Interviewing, Offer)',
      'Record interview rounds, recruiter notes, and links',
      'Centralized dashboard for all internship and full-time leads'
    ]
  },
  {
    badge: 'Module 1 & 5',
    badgeBg: '#f0f9ff',
    badgeColor: '#0284c7',
    title: 'Identify Skill Gaps',
    description:
      'Analyze job descriptions to discover key competencies, domain keywords, and technologies required by hiring teams.',
    icon: Target,
    features: [
      'Extract required vs preferred qualifications',
      'Pinpoint missing skills to learn before technical rounds',
      'Receive targeted career prep recommendations'
    ]
  },
  {
    badge: 'Module 3 & 4',
    badgeBg: '#faf5ff',
    badgeColor: '#9333ea',
    title: 'Prepare for Interviews',
    description:
      'Build confidence through systematic practice of company-specific technical and behavioral questions.',
    icon: MessageSquareCode,
    features: [
      'Filter questions by category and interview round',
      'Draft and refine personal STAR-method responses',
      'Track question mastery status from draft to perfected'
    ]
  }
];

const days = [
  { day: 'Day 1', name: 'Foundation & UI', active: false, done: true },
  { day: 'Day 2', name: 'App Tracker', active: false, done: true },
  { day: 'Day 3', name: 'JD Analyzer', active: false, done: true },
  { day: 'Day 4', name: 'Question Bank', active: true, done: false },
  { day: 'Day 5', name: 'Practice Studio', active: false },
  { day: 'Day 6', name: 'Recommendations', active: false },
  { day: 'Day 7', name: 'Polish & Review', active: false }
];

export default function OverviewSection() {
  return (
    <section className="fade-in">
      <div className="section-header">
        <h2 className="section-title">Preparation Overview</h2>
        <p className="section-desc">
          How SkillBridge guides your journey from job search to accepted offer.
        </p>
      </div>

      <div className="overview-grid">
        {pillars.map((pillar) => {
          const Icon = pillar.icon;
          return (
            <div key={pillar.title} className="overview-card">
              <div
                className="overview-pillar-badge"
                style={{
                  backgroundColor: pillar.badgeBg,
                  color: pillar.badgeColor
                }}
              >
                <Icon size={14} />
                <span>{pillar.badge}</span>
              </div>
              <div>
                <h3>{pillar.title}</h3>
                <p>{pillar.description}</p>
              </div>
              <ul className="overview-feature-list">
                {pillar.features.map((feat, idx) => (
                  <li key={idx} className="overview-feature-item">
                    <span className="overview-check-icon">
                      <CheckCircle2 size={12} />
                    </span>
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      {/* 7-Day Roadmap Strip */}
      <div className="roadmap-strip" style={{ marginTop: '1.5rem' }}>
        <div className="roadmap-header">
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              7-Day Development Roadmap
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Currently in Day 4: Interview Memory Bank & Practice Repository.
            </p>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: 'var(--primary)',
              background: 'var(--primary-light)',
              padding: '0.25rem 0.6rem',
              borderRadius: 'var(--radius-sm)'
            }}
          >
            <CalendarDays size={14} />
            <span>Sprint 1 / Day 4</span>
          </div>
        </div>

        <div className="roadmap-steps">
          {days.map((item) => (
            <div
              key={item.day}
              className={`roadmap-step ${item.active ? 'active' : ''}`}
            >
              <div className="roadmap-step-day">{item.day}</div>
              <div className="roadmap-step-name">{item.name}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
