import React, { useState, useEffect } from 'react';
import {
  X,
  HelpCircle,
  Briefcase,
  Calendar,
  Tag,
  BookOpen,
  Award,
  AlertCircle
} from 'lucide-react';

const ROUND_TYPES = ['Technical', 'HR', 'Aptitude', 'Behavioral', 'System Design'];
const DIFFICULTIES = ['Beginner', 'Intermediate', 'Advanced'];
const SOURCES = ['Personal interview', 'Recruiter', 'Online assessment', 'Peer', 'Other'];
const REVIEW_STATUSES = ['New', 'Learning', 'Confident'];

const SUGGESTED_TOPICS = [
  'Python',
  'JavaScript',
  'React',
  'SQL',
  'Data Structures & Algorithms',
  'System Design',
  'REST APIs',
  'Git',
  'Behavioral / STAR Method',
  'Conflict Resolution',
  'Teamwork & Leadership',
  'OOP Concepts'
];

const SUGGESTED_TAGS = [
  'LeetCode',
  'Live Coding',
  'System Architecture',
  'STAR Framework',
  'Strengths & Weaknesses',
  'Database Indexing',
  'Recursion',
  'Async / Await'
];

export default function QuestionModal({
  isOpen,
  onClose,
  onSave,
  initialQuestion = null,
  savedJobs = []
}) {
  const [formData, setFormData] = useState({
    question_text: '',
    round_type: 'Technical',
    topic: '',
    difficulty: 'Intermediate',
    company_name: '',
    job_role: '',
    job_id: '',
    interview_date: '',
    source: 'Personal interview',
    original_answer: '',
    expected_answer: '',
    improvement_notes: '',
    tags: '',
    review_status: 'New'
  });

  const [activeTab, setActiveTab] = useState('question');
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (initialQuestion) {
      setFormData({
        question_text: initialQuestion.question_text || '',
        round_type: initialQuestion.round_type || 'Technical',
        topic: initialQuestion.topic || '',
        difficulty: initialQuestion.difficulty || 'Intermediate',
        company_name: initialQuestion.company_name || '',
        job_role: initialQuestion.job_role || initialQuestion.job_title || '',
        job_id: initialQuestion.job_id ? String(initialQuestion.job_id) : '',
        interview_date: initialQuestion.interview_date ? initialQuestion.interview_date.split('T')[0] : '',
        source: initialQuestion.source || 'Personal interview',
        original_answer: initialQuestion.original_answer || initialQuestion.personal_answer || '',
        expected_answer: initialQuestion.expected_answer || '',
        improvement_notes: initialQuestion.improvement_notes || '',
        tags: initialQuestion.tags || '',
        review_status: initialQuestion.review_status || 'New'
      });
    } else {
      setFormData({
        question_text: '',
        round_type: 'Technical',
        topic: '',
        difficulty: 'Intermediate',
        company_name: '',
        job_role: '',
        job_id: '',
        interview_date: '',
        source: 'Personal interview',
        original_answer: '',
        expected_answer: '',
        improvement_notes: '',
        tags: '',
        review_status: 'New'
      });
    }
    setErrors({});
    setActiveTab('question');
  }, [initialQuestion, isOpen]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;

    // If job selection changes, auto-populate company and role if available
    if (name === 'job_id') {
      if (value) {
        const selectedJob = savedJobs.find((j) => String(j.id) === String(value));
        if (selectedJob) {
          setFormData((prev) => ({
            ...prev,
            job_id: value,
            company_name: prev.company_name || selectedJob.company_name,
            job_role: prev.job_role || selectedJob.job_title
          }));
          return;
        }
      }
      setFormData((prev) => ({ ...prev, job_id: value }));
      return;
    }

    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handleAddTopic = (topic) => {
    setFormData((prev) => ({ ...prev, topic }));
  };

  const handleAddTag = (tag) => {
    setFormData((prev) => {
      const currentTags = prev.tags ? prev.tags.split(',').map((t) => t.trim()).filter(Boolean) : [];
      if (!currentTags.includes(tag)) {
        return {
          ...prev,
          tags: currentTags.length > 0 ? `${prev.tags}, ${tag}` : tag
        };
      }
      return prev;
    });
  };

  const validate = () => {
    const errs = {};
    if (!formData.question_text.trim()) {
      errs.question_text = 'Question text is required.';
    } else if (formData.question_text.trim().length < 5) {
      errs.question_text = 'Question text must be at least 5 characters long.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) {
      setActiveTab('question');
      return;
    }

    setSubmitting(true);
    const payload = {
      question_text: formData.question_text.trim(),
      round_type: formData.round_type,
      topic: formData.topic.trim() || null,
      difficulty: formData.difficulty,
      company_name: formData.company_name.trim() || null,
      job_role: formData.job_role.trim() || null,
      job_id: formData.job_id ? parseInt(formData.job_id, 10) : null,
      interview_date: formData.interview_date || null,
      source: formData.source,
      original_answer: formData.original_answer.trim() || null,
      expected_answer: formData.expected_answer.trim() || null,
      improvement_notes: formData.improvement_notes.trim() || null,
      tags: formData.tags.trim() || null,
      review_status: formData.review_status
    };

    const res = await onSave(payload, initialQuestion?.id);
    setSubmitting(false);
    if (res && res.error) {
      setErrors({ form: res.error });
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-card"
        style={{ maxWidth: '680px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                background: 'var(--primary-light)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <HelpCircle size={18} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', margin: 0 }}>
                {initialQuestion ? 'Edit Interview Question' : 'Record Interview Question'}
              </h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                Save actual questions encountered in rounds and reflect on your answers.
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        {/* Modal Tabs */}
        <div className="modal-tabs">
          <button
            type="button"
            className={`modal-tab ${activeTab === 'question' ? 'active' : ''}`}
            onClick={() => setActiveTab('question')}
          >
            <HelpCircle size={14} />
            <span>1. Question & Category</span>
          </button>
          <button
            type="button"
            className={`modal-tab ${activeTab === 'context' ? 'active' : ''}`}
            onClick={() => setActiveTab('context')}
          >
            <Briefcase size={14} />
            <span>2. Company & Job Context</span>
          </button>
          <button
            type="button"
            className={`modal-tab ${activeTab === 'answers' ? 'active' : ''}`}
            onClick={() => setActiveTab('answers')}
          >
            <BookOpen size={14} />
            <span>3. Answers & Reflection</span>
          </button>
        </div>

        {errors.form && (
          <div className="alert-banner alert-danger" style={{ margin: '1rem 1.5rem 0' }}>
            <AlertCircle size={16} />
            <span>{errors.form}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
            {/* TAB 1: Question & Category */}
            {activeTab === 'question' && (
              <div className="fade-in">
                <div className="form-group">
                  <label htmlFor="q_text">
                    Question Text <span className="required-star">*</span>
                  </label>
                  <textarea
                    id="q_text"
                    name="question_text"
                    rows={4}
                    className={`form-input ${errors.question_text ? 'input-error' : ''}`}
                    placeholder="e.g., Explain the difference between useEffect and useLayoutEffect, and when would you use each?"
                    value={formData.question_text}
                    onChange={handleChange}
                    autoFocus
                  />
                  {errors.question_text && (
                    <span className="form-error-msg">{errors.question_text}</span>
                  )}
                </div>

                <div className="form-row-2">
                  <div className="form-group">
                    <label htmlFor="round_type">Round Type</label>
                    <select
                      id="round_type"
                      name="round_type"
                      className="form-input"
                      value={formData.round_type}
                      onChange={handleChange}
                    >
                      {ROUND_TYPES.map((rt) => (
                        <option key={rt} value={rt}>
                          {rt} Round
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="difficulty">Difficulty Level</label>
                    <select
                      id="difficulty"
                      name="difficulty"
                      className="form-input"
                      value={formData.difficulty}
                      onChange={handleChange}
                    >
                      {DIFFICULTIES.map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="topic">Topic / Subject</label>
                  <input
                    id="topic"
                    type="text"
                    name="topic"
                    className="form-input"
                    placeholder="e.g., React Hooks, SQL Joins, System Architecture, STAR Method"
                    value={formData.topic}
                    onChange={handleChange}
                  />
                  <div className="quick-chip-list">
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Suggestions:</span>
                    {SUGGESTED_TOPICS.map((top) => (
                      <button
                        type="button"
                        key={top}
                        className="quick-chip-btn"
                        onClick={() => handleAddTopic(top)}
                      >
                        {top}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Company & Job Context */}
            {activeTab === 'context' && (
              <div className="fade-in">
                <div className="form-group">
                  <label htmlFor="job_id">
                    Link to Saved Opportunity (Optional)
                  </label>
                  <select
                    id="job_id"
                    name="job_id"
                    className="form-input"
                    value={formData.job_id}
                    onChange={handleChange}
                  >
                    <option value="">-- Standalone (Not linked to a tracked job) --</option>
                    {savedJobs.map((job) => (
                      <option key={job.id} value={job.id}>
                        {job.company_name} — {job.job_title} ({job.application_status})
                      </option>
                    ))}
                  </select>
                  <span className="field-hint">
                    Linking copies company and role info, and lets you view interview questions directly from that application.
                  </span>
                </div>

                <div className="form-row-2">
                  <div className="form-group">
                    <label htmlFor="company_name">Company Name</label>
                    <input
                      id="company_name"
                      type="text"
                      name="company_name"
                      className="form-input"
                      placeholder="e.g., Google, Stripe, Microsoft"
                      value={formData.company_name}
                      onChange={handleChange}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="job_role">Job Role / Position</label>
                    <input
                      id="job_role"
                      type="text"
                      name="job_role"
                      className="form-input"
                      placeholder="e.g., Frontend Intern, Software Engineer"
                      value={formData.job_role}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="form-row-2">
                  <div className="form-group">
                    <label htmlFor="interview_date">Date Encountered</label>
                    <input
                      id="interview_date"
                      type="date"
                      name="interview_date"
                      className="form-input"
                      value={formData.interview_date}
                      onChange={handleChange}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="source">Question Source</label>
                    <select
                      id="source"
                      name="source"
                      className="form-input"
                      value={formData.source}
                      onChange={handleChange}
                    >
                      {SOURCES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="tags">Tags (Comma-separated)</label>
                  <input
                    id="tags"
                    type="text"
                    name="tags"
                    className="form-input"
                    placeholder="e.g., Live Coding, STAR Framework, Algorithms"
                    value={formData.tags}
                    onChange={handleChange}
                  />
                  <div className="quick-chip-list">
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Suggestions:</span>
                    {SUGGESTED_TAGS.map((t) => (
                      <button
                        type="button"
                        key={t}
                        className="quick-chip-btn"
                        onClick={() => handleAddTag(t)}
                      >
                        +{t}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: Answers & Reflection */}
            {activeTab === 'answers' && (
              <div className="fade-in">
                <div className="form-group">
                  <label htmlFor="review_status">Current Confidence / Review Status</label>
                  <select
                    id="review_status"
                    name="review_status"
                    className="form-input"
                    value={formData.review_status}
                    onChange={handleChange}
                  >
                    {REVIEW_STATUSES.map((st) => (
                      <option key={st} value={st}>
                        {st === 'New' && '🟡 New — Recently added, needs first review'}
                        {st === 'Learning' && '🟠 Learning — Practicing and improving answer'}
                        {st === 'Confident' && '🟢 Confident — Ready and mastered'}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="orig_answer">
                    My Original Answer or Notes
                  </label>
                  <textarea
                    id="orig_answer"
                    name="original_answer"
                    rows={3}
                    className="form-input"
                    placeholder="Write what you actually said in the interview or your initial rough thought process..."
                    value={formData.original_answer}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="exp_answer">
                    Expected Answer, Key Points & Frameworks
                  </label>
                  <textarea
                    id="exp_answer"
                    name="expected_answer"
                    rows={4}
                    className="form-input"
                    placeholder="Ideal points, code structure, time/space complexity, or STAR points (Situation, Task, Action, Result)..."
                    value={formData.expected_answer}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="imp_notes">
                    What I Need to Improve
                  </label>
                  <textarea
                    id="imp_notes"
                    name="improvement_notes"
                    rows={3}
                    className="form-input"
                    placeholder="e.g., Need to be more structured in explaining trade-offs; practice speaking concisely under 2 minutes..."
                    value={formData.improvement_notes}
                    onChange={handleChange}
                  />
                </div>
              </div>
            )}
          </div>

          <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {activeTab !== 'question' && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setActiveTab(activeTab === 'answers' ? 'context' : 'question')}
                >
                  Back
                </button>
              )}
              {activeTab !== 'answers' && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setActiveTab(activeTab === 'question' ? 'context' : 'answers')}
                >
                  Next Step
                </button>
              )}
            </div>

            <div style={{ display: 'flex', gap: '0.6rem' }}>
              <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={submitting}>
                {submitting ? 'Saving...' : initialQuestion ? 'Update Question' : 'Save Question'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
