import React from 'react';
import {
  X,
  HelpCircle,
  Building,
  Briefcase,
  Calendar,
  Tag,
  CheckCircle2,
  Edit2,
  Trash2,
  ExternalLink,
  BookOpen,
  Sparkles,
  ArrowRight
} from 'lucide-react';

export default function QuestionDetailModal({
  isOpen,
  onClose,
  question,
  onEdit,
  onDelete,
  onStatusChange,
  onNavigateToJob
}) {
  if (!isOpen || !question) return null;

  const roundBadgeClass = `badge-round-${(question.round_type || 'technical').toLowerCase().replace(/\s+/g, '-')}`;
  const diffBadgeClass = `badge-diff-${(question.difficulty || 'intermediate').toLowerCase()}`;
  const statusBadgeClass = `badge-status-${(question.review_status || 'new').toLowerCase()}`;

  const tagsList = question.tags
    ? question.tags.split(',').map((t) => t.trim()).filter(Boolean)
    : [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-card"
        style={{ maxWidth: '720px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'var(--primary-light)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <HelpCircle size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span className={`q-badge ${roundBadgeClass}`}>
                  {question.round_type} Round
                </span>
                <span className={`q-badge ${diffBadgeClass}`}>
                  {question.difficulty}
                </span>
                <span className={`q-badge ${statusBadgeClass}`}>
                  {question.review_status}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0.2rem 0 0' }}>
                Encountered {question.interview_date ? `on ${question.interview_date}` : 'in interview'}{' '}
                {question.source ? `via ${question.source}` : ''}
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body" style={{ maxHeight: '68vh', overflowY: 'auto' }}>
          {/* Question Text */}
          <div className="detail-question-box">
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)', margin: '0 0 0.5rem', lineHeight: 1.5 }}>
              {question.question_text}
            </h3>

            {/* Context meta row */}
            <div className="detail-meta-row">
              {question.company_name && (
                <div className="detail-meta-item">
                  <Building size={14} />
                  <span>
                    <strong>{question.company_name}</strong>
                    {question.job_role && ` — ${question.job_role}`}
                  </span>
                </div>
              )}

              {question.topic && (
                <div className="detail-meta-item">
                  <Tag size={14} />
                  <span>Topic: <strong>{question.topic}</strong></span>
                </div>
              )}

              {question.job_id && onNavigateToJob && (
                <button
                  type="button"
                  className="linked-job-btn"
                  onClick={() => onNavigateToJob(question.job_id)}
                >
                  <Briefcase size={13} />
                  <span>View Tracked Job #{question.job_id}</span>
                  <ExternalLink size={12} />
                </button>
              )}
            </div>

            {tagsList.length > 0 && (
              <div className="q-tags-container" style={{ marginTop: '0.6rem' }}>
                {tagsList.map((tag, idx) => (
                  <span key={idx} className="q-tag-pill">
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Quick status switcher */}
          <div className="detail-status-bar">
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Confidence & Mastery Status:
            </span>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              {['New', 'Learning', 'Confident'].map((st) => (
                <button
                  key={st}
                  type="button"
                  className={`status-pill-btn ${question.review_status === st ? 'active' : ''}`}
                  onClick={() => onStatusChange(question.id, st)}
                >
                  {st === 'Confident' && '✓ '}
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Section 1: Original Answer Notes */}
          <div className="detail-section-card">
            <div className="detail-section-header">
              <span className="detail-section-icon" style={{ background: 'var(--primary-light)', color: 'var(--primary)' }}>
                <BookOpen size={15} />
              </span>
              <h4>My Original Answer & Response Notes</h4>
            </div>
            {question.original_answer || question.personal_answer ? (
              <p className="detail-section-content">
                {question.original_answer || question.personal_answer}
              </p>
            ) : (
              <p className="detail-section-empty">
                No original answer notes recorded. Click "Edit Question" to add what you said or your live thought process.
              </p>
            )}
          </div>

          {/* Section 2: Expected Answer & Frameworks */}
          <div className="detail-section-card">
            <div className="detail-section-header">
              <span className="detail-section-icon" style={{ background: '#ecfdf5', color: '#10b981' }}>
                <Sparkles size={15} />
              </span>
              <h4>Expected Answer, Key Points & References</h4>
            </div>
            {question.expected_answer ? (
              <p className="detail-section-content">
                {question.expected_answer}
              </p>
            ) : (
              <p className="detail-section-empty">
                No reference answer notes added yet. Record the ideal solution, time complexities, or STAR points.
              </p>
            )}
          </div>

          {/* Section 3: Improvement Notes */}
          <div className="detail-section-card">
            <div className="detail-section-header">
              <span className="detail-section-icon" style={{ background: '#fffbeb', color: '#f59e0b' }}>
                <ArrowRight size={15} />
              </span>
              <h4>What I Need to Improve (Next Time)</h4>
            </div>
            {question.improvement_notes ? (
              <p className="detail-section-content">
                {question.improvement_notes}
              </p>
            ) : (
              <p className="detail-section-empty">
                No improvement notes written yet. Document areas where you stumbled to avoid repeating the mistake.
              </p>
            )}
          </div>
        </div>

        <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
          <button
            type="button"
            className="btn-danger-outline"
            onClick={() => {
              onClose();
              onDelete(question);
            }}
          >
            <Trash2 size={15} />
            <span>Delete</span>
          </button>

          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Close
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={() => {
                onClose();
                onEdit(question);
              }}
            >
              <Edit2 size={15} />
              <span>Edit Question</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
