import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bookmark,
  Send,
  Calendar,
  Award,
  Sparkles,
  AlertTriangle,
  ArrowRight,
  Plus,
  Clock,
  HelpCircle,
  Mic,
  FileSearch,
  CheckCircle2,
  TrendingUp,
  Target,
  ExternalLink,
  Play,
  RefreshCw,
  AlertCircle,
  FileText
} from 'lucide-react';
import SummaryCard from '../components/SummaryCard';
import QuickActions from '../components/QuickActions';
import JobModal from '../components/JobModal';
import { getDashboardSummary } from '../services/api';

export default function Dashboard() {
  const navigate = useNavigate();

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAddJobOpen, setIsAddJobOpen] = useState(false);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await getDashboardSummary();
    if (res.ok && res.data) {
      setDashboardData(res.data);
    } else {
      setError(res.error || 'Failed to load dashboard metrics.');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  const cards = dashboardData?.summary_cards || {
    total_saved_jobs: 0,
    applications_submitted: 0,
    interviews_in_progress: 0,
    offers_received: 0,
    rejected_count: 0,
    withdrawn_count: 0,
    total_jobs: 0,
    upcoming_deadlines_count: 0,
    total_questions_saved: 0,
    questions_confident: 0,
    questions_learning: 0,
    sessions_completed: 0,
    sessions_in_progress: 0,
    average_self_assessment: null
  };

  const primaryCards = [
    {
      title: 'Saved Opportunities',
      value: cards.total_saved_jobs,
      icon: Bookmark,
      iconBg: '#e0f2fe',
      iconColor: '#0284c7',
      tagText: 'Saved Stage',
      subtext: `${cards.total_saved_jobs} jobs pending submission`,
      onClick: () => navigate('/applications?status=Saved')
    },
    {
      title: 'Submitted Applications',
      value: cards.applications_submitted,
      icon: Send,
      iconBg: '#e0e7ff',
      iconColor: '#4338ca',
      tagText: 'Applied Stage',
      subtext: `${cards.applications_submitted} active submissions`,
      onClick: () => navigate('/applications?status=Applied')
    },
    {
      title: 'Active Interviews',
      value: cards.interviews_in_progress,
      icon: Calendar,
      iconBg: '#fef3c7',
      iconColor: '#b45309',
      tagText: 'Assessment & Rounds',
      subtext: `${cards.interviews_in_progress} opportunities in progress`,
      onClick: () => navigate('/applications?status=Interview')
    },
    {
      title: 'Job Offers Extended',
      value: cards.offers_received,
      icon: Award,
      iconBg: '#d1fae5',
      iconColor: '#047857',
      tagText: 'Offers Stage',
      subtext: `${cards.offers_received} extended offer(s)`,
      onClick: () => navigate('/applications?status=Offer')
    },
    {
      title: 'Interview Questions',
      value: cards.total_questions_saved,
      icon: HelpCircle,
      iconBg: '#faf5ff',
      iconColor: '#7c3aed',
      tagText: 'Memory Bank',
      subtext: `${cards.questions_confident} marked Confident`,
      onClick: () => navigate('/questions')
    },
    {
      title: 'Mock Sessions Run',
      value: cards.sessions_completed,
      icon: Mic,
      iconBg: '#eff6ff',
      iconColor: '#2563eb',
      tagText: 'Practice Studio',
      subtext: cards.average_self_assessment
        ? `Avg Rating: ${cards.average_self_assessment}/5`
        : 'Self-assessment tracking',
      onClick: () => navigate('/practice')
    }
  ];

  return (
    <div className="dashboard-page fade-in">
      {/* 1. Welcome Section */}
      <section className="welcome-hero">
        <div className="welcome-badge">
          <Sparkles size={14} />
          <span>SkillBridge &bull; Unified Career Preparation Workspace</span>
        </div>
        <h1 className="welcome-title">Student Career Preparation Dashboard</h1>
        <p className="welcome-subtitle">
          Your integrated placement hub. Track applications, identify technical skill gaps,
          store company-specific interview experiences, and simulate mock rounds with structured self-reviews.
        </p>
      </section>

      {/* Error Banner if API fails */}
      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', padding: '1rem', borderRadius: '8px', color: '#b91c1c', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
          <button className="btn-secondary" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }} onClick={fetchSummary}>
            <RefreshCw size={14} style={{ display: 'inline', marginRight: '4px' }} /> Retry
          </button>
        </div>
      )}

      {/* Overdue/Approaching Deadlines Alert Banner */}
      {cards.upcoming_deadlines_count > 0 && (
        <div className="deadline-alert-banner">
          <div className="deadline-alert-content">
            <AlertTriangle size={20} className="deadline-alert-icon" />
            <div>
              <strong>Action Required: {cards.upcoming_deadlines_count} Approaching or Overdue Deadline{cards.upcoming_deadlines_count > 1 ? 's' : ''}!</strong>
              <div>You have job applications with submission deadlines requiring immediate attention.</div>
            </div>
          </div>
          <button
            className="btn-primary"
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
            onClick={() => navigate('/applications')}
          >
            <span>Review Applications</span>
            <ArrowRight size={14} />
          </button>
        </div>
      )}

      {/* 2. Real-time Summary Cards */}
      <section>
        <div className="section-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 className="section-title">Preparation & Pipeline Metrics</h2>
            <p className="section-desc">
              Live statistics calculated directly from your stored jobs, analyses, memory bank, and practice sessions.
            </p>
          </div>
          <button
            className="btn-primary"
            onClick={() => setIsAddJobOpen(true)}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.825rem' }}
          >
            <Plus size={16} />
            <span>Add Job</span>
          </button>
        </div>

        <div className="summary-grid">
          {primaryCards.map((card) => (
            <div
              key={card.title}
              onClick={card.onClick}
              style={{ cursor: 'pointer' }}
              title={`Click to view ${card.title}`}
            >
              <SummaryCard
                title={card.title}
                value={loading ? '...' : card.value}
                icon={card.icon}
                iconBg={card.iconBg}
                iconColor={card.iconColor}
                tagText={card.tagText}
                subtext={card.subtext}
              />
            </div>
          ))}
        </div>
      </section>

      {/* 3. Application Funnel Pipeline */}
      <section className="dashboard-card">
        <div className="dashboard-card-header">
          <div className="dashboard-card-title">
            <TrendingUp size={18} color="#2563eb" /> Application Pipeline Funnel
          </div>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Total Pipeline: {cards.total_jobs} Opportunities
          </span>
        </div>

        <div className="funnel-container">
          <div className="funnel-pipeline-row">
            {dashboardData?.application_funnel?.pipeline?.map((stage) => (
              <div
                key={stage.stage}
                className="funnel-stage-card"
                onClick={() => navigate(`/applications?status=${stage.stage}`)}
                title={`Filter applications by ${stage.label}`}
              >
                <span className="funnel-stage-count" style={{ color: stage.color }}>
                  {loading ? '...' : stage.count}
                </span>
                <span className="funnel-stage-name">{stage.label}</span>
              </div>
            ))}
          </div>

          <div className="funnel-outcomes-row">
            <span style={{ fontSize: '0.75rem', color: '#64748b', alignSelf: 'center', marginRight: '0.25rem' }}>
              Final Outcomes:
            </span>
            {dashboardData?.application_funnel?.outcomes?.map((outcome) => (
              <div
                key={outcome.stage}
                className="funnel-outcome-pill"
                onClick={() => navigate(`/applications?status=${outcome.stage}`)}
                title={`Filter applications by ${outcome.label}`}
              >
                <span style={{ fontWeight: 700, color: outcome.color }}>
                  {loading ? '...' : outcome.count}
                </span>
                <span>{outcome.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Two-Column Split: Deadlines & Skill Gaps vs Interview Prep */}
      <div className="dashboard-split-grid">
        {/* Left Column: Upcoming Deadlines & Skill Gaps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Upcoming Deadlines */}
          <section className="dashboard-card">
            <div className="dashboard-card-header">
              <div className="dashboard-card-title">
                <Clock size={18} color="#b45309" /> Upcoming Deadlines
              </div>
              <button
                className="dashboard-card-action-link"
                onClick={() => navigate('/applications')}
              >
                View Tracker <ArrowRight size={12} />
              </button>
            </div>

            {dashboardData?.upcoming_deadlines?.length > 0 ? (
              <div className="deadlines-list">
                {dashboardData.upcoming_deadlines.slice(0, 4).map((d) => (
                  <div key={d.id} className="deadline-row-card">
                    <div className="deadline-info">
                      <h4>{d.company_name}</h4>
                      <p>{d.job_title} &bull; {d.application_status}</p>
                    </div>
                    <div className="deadline-meta">
                      <span className={`urgency-badge ${d.urgency}`}>
                        {d.is_overdue
                          ? `${Math.abs(d.days_remaining)}d Overdue`
                          : d.days_remaining === 0
                          ? 'Today'
                          : `${d.days_remaining}d Left`}
                      </span>
                      <button
                        className="btn-secondary"
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        onClick={() => navigate(`/applications?search=${d.company_name}`)}
                        title="View job details"
                      >
                        <ExternalLink size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: '#64748b', fontSize: '0.85rem' }}>
                <CheckCircle2 size={24} color="#059669" style={{ marginBottom: '0.35rem' }} />
                <p>No urgent deadlines right now. Keep exploring new opportunities!</p>
              </div>
            )}
          </section>

          {/* Skill-Gap Overview */}
          <section className="dashboard-card">
            <div className="dashboard-card-header">
              <div className="dashboard-card-title">
                <Target size={18} color="#4338ca" /> Skill-Gap Overview
              </div>
              <button
                className="dashboard-card-action-link"
                onClick={() => navigate('/job-analyzer')}
              >
                Job Analyzer <ArrowRight size={12} />
              </button>
            </div>

            <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '-0.5rem 0 0.5rem 0' }}>
              Aggregated from {dashboardData?.skill_gap_summary?.total_analyses || 0} saved job description analyses.
            </p>

            {dashboardData?.skill_gap_summary?.frequently_missing_required?.length > 0 ? (
              <div className="skill-gap-list">
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#334155' }}>
                  Frequently Missing Required Skills:
                </span>
                {dashboardData.skill_gap_summary.frequently_missing_required.slice(0, 3).map((gap) => (
                  <div key={gap.skill} className="skill-gap-item">
                    <div>
                      <span className="skill-name-tag">{gap.skill}</span>
                      <div className="skill-job-chips">
                        Required in {gap.frequency} analysis &bull; {gap.associated_jobs.join(', ')}
                      </div>
                    </div>
                    <button
                      className="btn-secondary"
                      style={{ padding: '0.25rem 0.55rem', fontSize: '0.75rem' }}
                      onClick={() => navigate(`/questions?search=${gap.skill}`)}
                      title={`Search interview questions on ${gap.skill}`}
                    >
                      Prep Skill
                    </button>
                  </div>
                ))}

                {dashboardData?.skill_gap_summary?.suggested_learning_tasks?.length > 0 && (
                  <div className="learning-tasks-list">
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginTop: '0.25rem' }}>
                      Recommended Action:
                    </span>
                    <div className="learning-task-card">
                      {dashboardData.skill_gap_summary.suggested_learning_tasks[0].task}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: '#64748b', fontSize: '0.85rem' }}>
                <FileSearch size={24} style={{ opacity: 0.5, marginBottom: '0.35rem' }} />
                <p>No skill analyses saved yet. Analyze job descriptions to discover key missing qualifications.</p>
                <button
                  className="btn-primary"
                  style={{ marginTop: '0.75rem', padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
                  onClick={() => navigate('/job-analyzer')}
                >
                  Analyze Job Description
                </button>
              </div>
            )}
          </section>
        </div>

        {/* Right Column: Interview Preparation Overview */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <section className="dashboard-card">
            <div className="dashboard-card-header">
              <div className="dashboard-card-title">
                <HelpCircle size={18} color="#7c3aed" /> Interview Preparation Overview
              </div>
              <button
                className="dashboard-card-action-link"
                onClick={() => navigate('/questions')}
              >
                Question Bank <ArrowRight size={12} />
              </button>
            </div>

            {/* Questions Mastery Ratio */}
            <div className="prep-mastery-strip">
              <div className="mastery-stat-item">
                <h5 style={{ color: '#059669' }}>{cards.questions_confident}</h5>
                <p>Confident</p>
              </div>
              <div className="mastery-stat-item">
                <h5 style={{ color: '#b45309' }}>{cards.questions_learning}</h5>
                <p>Learning / New</p>
              </div>
              <div className="mastery-stat-item">
                <h5 style={{ color: '#2563eb' }}>{cards.total_questions_saved}</h5>
                <p>Total Saved</p>
              </div>
            </div>

            {/* Active Practice Session Resume Banner */}
            {dashboardData?.interview_prep_summary?.active_session_to_resume && (
              <div className="resume-session-banner">
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#2563eb', textTransform: 'uppercase' }}>
                    In-Progress Interview Session
                  </div>
                  <strong style={{ fontSize: '0.9rem', color: '#0f172a' }}>
                    {dashboardData.interview_prep_summary.active_session_to_resume.session_name}
                  </strong>
                  <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                    Paused on Question {dashboardData.interview_prep_summary.active_session_to_resume.current_index + 1} of {dashboardData.interview_prep_summary.active_session_to_resume.total_questions} ({dashboardData.interview_prep_summary.active_session_to_resume.round_type})
                  </div>
                </div>
                <button
                  className="btn-primary"
                  style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
                  onClick={() => navigate('/practice')}
                >
                  <Play size={14} /> Resume Session
                </button>
              </div>
            )}

            {/* Topics Needing Practice */}
            {dashboardData?.interview_prep_summary?.topics_needing_practice?.length > 0 && (
              <div>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#334155' }}>
                  Topics Needing Revision:
                </span>
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.4rem' }}>
                  {dashboardData.interview_prep_summary.topics_needing_practice.map((item) => (
                    <button
                      key={item.topic}
                      className="pill-option-btn"
                      style={{ fontSize: '0.78rem', padding: '0.3rem 0.6rem' }}
                      onClick={() => navigate(`/questions?topic=${item.topic}`)}
                      title={`Review ${item.unmastered_count} unmastered questions in ${item.topic}`}
                    >
                      {item.topic} ({item.unmastered_count})
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Practice Sessions */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#334155' }}>
                  Recent Mock Sessions:
                </span>
                <button
                  className="dashboard-card-action-link"
                  style={{ fontSize: '0.75rem' }}
                  onClick={() => navigate('/practice')}
                >
                  Start New Session
                </button>
              </div>

              {dashboardData?.interview_prep_summary?.recent_sessions?.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {dashboardData.interview_prep_summary.recent_sessions.map((session) => (
                    <div
                      key={session.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.6rem 0.75rem',
                        background: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                        fontSize: '0.825rem'
                      }}
                    >
                      <div>
                        <strong>{session.session_name}</strong>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                          {session.round_type} &bull; {session.attempted_count}/{session.total_questions} answered &bull; {session.date}
                        </div>
                      </div>
                      <span className={`status-badge ${session.status.toLowerCase().replace(/\s+/g, '-')}`}>
                        {session.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '1.25rem', color: '#64748b', fontSize: '0.825rem' }}>
                  <Mic size={20} style={{ opacity: 0.5, marginBottom: '0.25rem' }} />
                  <p>No mock sessions run yet. Rehearse real interview rounds under timed conditions.</p>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>

      {/* 4.5. Compact ATS Resume Overview */}
      <section className="dashboard-card" style={{ marginBottom: '1.5rem' }}>
        <div className="dashboard-card-header">
          <div className="dashboard-card-title">
            <FileText size={18} color="#4f46e5" /> ATS Resume Management
          </div>
          <button
            className="dashboard-card-action-link"
            onClick={() => navigate('/resume-builder')}
          >
            Resume Workspace <ArrowRight size={12} />
          </button>
        </div>

        {dashboardData?.resume_overview?.most_recent_resume ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', padding: '0.5rem 0' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <strong style={{ fontSize: '1.05rem', color: '#0f172a' }}>
                  {dashboardData.resume_overview.most_recent_resume.title}
                </strong>
                {dashboardData.resume_overview.most_recent_resume.target_role && (
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, background: '#eef2ff', color: '#4f46e5', padding: '0.2rem 0.6rem', borderRadius: '999px' }}>
                    {dashboardData.resume_overview.most_recent_resume.target_role}
                  </span>
                )}
                {dashboardData.resume_overview.most_recent_resume.target_company && (
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, background: '#f0fdf4', color: '#166534', padding: '0.2rem 0.6rem', borderRadius: '999px' }}>
                    Tailored for {dashboardData.resume_overview.most_recent_resume.target_company}
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.825rem', color: '#64748b' }}>
                Saved Drafts: <strong>{dashboardData.resume_overview.total_resumes}</strong> &bull;{' '}
                Completeness Score: <strong>{dashboardData.resume_overview.most_recent_resume.completeness_score || 0}/100</strong> &bull;{' '}
                {dashboardData.resume_overview.most_recent_resume.has_unresolved_warnings ? (
                  <span style={{ color: '#dc2626', fontWeight: 600 }}>
                    ⚠️ {dashboardData.resume_overview.most_recent_resume.critical_issues_count} review warning(s) unresolved
                  </span>
                ) : (
                  <span style={{ color: '#16a34a', fontWeight: 600 }}>
                    ✓ No critical review warnings
                  </span>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button
                className="btn-primary"
                style={{ padding: '0.45rem 0.85rem', fontSize: '0.825rem' }}
                onClick={() => navigate(`/resume-builder?id=${dashboardData.resume_overview.most_recent_resume.id}`)}
              >
                Continue Editing
              </button>
              <button
                className="btn-secondary"
                style={{ padding: '0.45rem 0.85rem', fontSize: '0.825rem', background: '#f1f5f9', color: '#334155' }}
                onClick={() => navigate(`/resume-builder?id=${dashboardData.resume_overview.most_recent_resume.id}&tab=review`)}
              >
                Review Quality
              </button>
              {dashboardData.resume_overview.most_recent_resume.target_job_id && (
                <button
                  className="btn-secondary"
                  style={{ padding: '0.45rem 0.85rem', fontSize: '0.825rem', background: '#eef2ff', color: '#4f46e5' }}
                  onClick={() => navigate(`/applications?search=${encodeURIComponent(dashboardData.resume_overview.most_recent_resume.target_company || '')}`)}
                >
                  View Target Job
                </button>
              )}
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '1.5rem', color: '#64748b', fontSize: '0.875rem' }}>
            <FileText size={24} style={{ opacity: 0.5, marginBottom: '0.35rem' }} />
            <p>No resume drafts saved yet. Create your first ATS-friendly single-column resume.</p>
            <button
              className="btn-primary"
              style={{ marginTop: '0.75rem', padding: '0.45rem 1rem', fontSize: '0.825rem' }}
              onClick={() => navigate('/resume-builder')}
            >
              <Plus size={14} /> Create ATS Resume
            </button>
          </div>
        )}
      </section>

      {/* 5. Personalized Next-Action List (Recommended Next Steps) */}
      <section className="dashboard-card">
        <div className="dashboard-card-header">
          <div className="dashboard-card-title">
            <Sparkles size={18} color="#2563eb" /> Recommended Next Steps
          </div>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Personalized guidance based on your real application and preparation records
          </span>
        </div>

        <div className="recommendations-grid">
          {dashboardData?.recommended_next_steps?.map((rec) => (
            <div key={rec.id} className="rec-card">
              <div className="rec-card-top">
                <span className={`rec-priority-badge ${rec.priority}`}>
                  {rec.priority} Priority
                </span>
                <h4 className="rec-card-title">{rec.title}</h4>
                <p className="rec-card-desc">{rec.description}</p>
              </div>
              <button
                className="rec-action-btn"
                onClick={() => navigate(rec.action_link)}
              >
                <span>{rec.action_text}</span>
                <ArrowRight size={14} />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* 6. Quick Actions */}
      <QuickActions onOpenAddJob={() => setIsAddJobOpen(true)} />

      {/* Add Job Modal accessible from Dashboard */}
      <JobModal
        isOpen={isAddJobOpen}
        onClose={() => setIsAddJobOpen(false)}
        onSaved={() => {
          setIsAddJobOpen(false);
          fetchSummary();
        }}
      />
    </div>
  );
}
