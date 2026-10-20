import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  HelpCircle,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Code,
  Users,
  Building,
  Calendar,
  Edit2,
  Trash2,
  ArrowUpDown,
  BookOpen,
  AlertTriangle,
  Mic,
  ExternalLink
} from 'lucide-react';
import {
  getQuestions,
  getQuestionStats,
  createQuestion,
  updateQuestion,
  updateQuestionStatus,
  deleteQuestion,
  getApplications
} from '../services/api';
import QuestionModal from '../components/QuestionModal';
import QuestionDetailModal from '../components/QuestionDetailModal';
import '../styles/questions.css';

const ROUND_TABS = [
  { id: 'All', label: 'All Rounds' },
  { id: 'Technical', label: 'Technical' },
  { id: 'HR', label: 'HR' },
  { id: 'Behavioral', label: 'Behavioral' },
  { id: 'System Design', label: 'System Design' },
  { id: 'Aptitude', label: 'Aptitude' }
];

export default function InterviewQuestions() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // URL parameters for cross-module filtering
  const urlSearch = searchParams.get('search') || '';
  const urlRound = searchParams.get('round_type') || 'All';
  const urlDiff = searchParams.get('difficulty') || 'All';
  const urlStatus = searchParams.get('review_status') || 'All';
  const urlCompany = searchParams.get('company_name') || searchParams.get('company') || 'All';
  const urlTopic = searchParams.get('topic') || 'All';
  const urlJobId = searchParams.get('job_id') || '';

  // Core Data
  const [questions, setQuestions] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    technical: 0,
    hr_behavioral: 0,
    confident: 0,
    needs_review: 0,
    by_round: {},
    by_status: {},
    by_difficulty: {}
  });
  const [savedJobs, setSavedJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Search
  const [selectedRound, setSelectedRound] = useState(urlRound);
  const [searchQuery, setSearchQuery] = useState(urlSearch);
  const [difficultyFilter, setDifficultyFilter] = useState(urlDiff);
  const [statusFilter, setStatusFilter] = useState(urlStatus);
  const [companyFilter, setCompanyFilter] = useState(urlCompany);
  const [topicFilter, setTopicFilter] = useState(urlTopic);
  const [jobIdFilter, setJobIdFilter] = useState(urlJobId);
  const [sortBy, setSortBy] = useState('recent');
  const [sortOrder, setSortOrder] = useState('desc');

  // Sync state if URL params change
  useEffect(() => {
    if (urlSearch) setSearchQuery(urlSearch);
    if (urlRound && urlRound !== 'All') setSelectedRound(urlRound);
    if (urlDiff && urlDiff !== 'All') setDifficultyFilter(urlDiff);
    if (urlStatus && urlStatus !== 'All') setStatusFilter(urlStatus);
    if (urlCompany && urlCompany !== 'All') setCompanyFilter(urlCompany);
    if (urlTopic && urlTopic !== 'All') setTopicFilter(urlTopic);
    if (urlJobId) setJobIdFilter(urlJobId);
  }, [urlSearch, urlRound, urlDiff, urlStatus, urlCompany, urlTopic, urlJobId]);

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [detailQuestion, setDetailQuestion] = useState(null);
  const [deletingQuestion, setDeletingQuestion] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch Questions & Stats
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    const [qRes, statsRes, jobsRes] = await Promise.all([
      getQuestions({
        search: searchQuery,
        round_type: selectedRound !== 'All' ? selectedRound : undefined,
        difficulty: difficultyFilter !== 'All' ? difficultyFilter : undefined,
        review_status: statusFilter !== 'All' ? statusFilter : undefined,
        company_name: companyFilter !== 'All' ? companyFilter : undefined,
        topic: topicFilter !== 'All' ? topicFilter : undefined,
        job_id: jobIdFilter ? parseInt(jobIdFilter, 10) : undefined,
        sort_by: sortBy,
        order: sortOrder
      }),
      getQuestionStats(),
      getApplications()
    ]);

    if (qRes.ok) {
      setQuestions(qRes.data || []);
    } else {
      setError(qRes.error || 'Failed to load interview questions');
    }

    if (statsRes.ok && statsRes.data) {
      setStats(statsRes.data);
    }

    if (jobsRes.ok && jobsRes.data) {
      setSavedJobs(jobsRes.data);
    }

    setLoading(false);
  }, [
    searchQuery,
    selectedRound,
    difficultyFilter,
    statusFilter,
    companyFilter,
    topicFilter,
    jobIdFilter,
    sortBy,
    sortOrder
  ]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Extract unique companies & topics for dropdown filter lists
  const availableCompanies = useMemo(() => {
    const set = new Set();
    questions.forEach((q) => {
      if (q.company_name) set.add(q.company_name);
    });
    return Array.from(set).sort();
  }, [questions]);

  const availableTopics = useMemo(() => {
    const set = new Set();
    questions.forEach((q) => {
      if (q.topic) set.add(q.topic);
    });
    return Array.from(set).sort();
  }, [questions]);

  // Handle Save (Create or Update)
  const handleSaveQuestion = async (payload, id) => {
    let res;
    if (id) {
      res = await updateQuestion(id, payload);
    } else {
      res = await createQuestion(payload);
    }

    if (res.ok) {
      setIsModalOpen(false);
      setEditingQuestion(null);
      fetchData();
      return { ok: true };
    } else {
      return { error: res.error || 'Failed to save question' };
    }
  };

  // Handle Quick Status Change
  const handleQuickStatusChange = async (id, newStatus) => {
    const res = await updateQuestionStatus(id, newStatus);
    if (res.ok) {
      // Optimistic update
      setQuestions((prev) =>
        prev.map((q) => (q.id === id ? { ...q, review_status: newStatus } : q))
      );
      if (detailQuestion && detailQuestion.id === id) {
        setDetailQuestion((prev) => ({ ...prev, review_status: newStatus }));
      }
      // Refresh stats
      const statsRes = await getQuestionStats();
      if (statsRes.ok) setStats(statsRes.data);
    }
  };

  // Handle Delete Confirmation
  const handleDeleteConfirm = async () => {
    if (!deletingQuestion) return;
    setIsDeleting(true);
    const res = await deleteQuestion(deletingQuestion.id);
    setIsDeleting(false);
    if (res.ok) {
      setDeletingQuestion(null);
      if (detailQuestion && detailQuestion.id === deletingQuestion.id) {
        setDetailQuestion(null);
      }
      fetchData();
    } else {
      alert(`Error deleting question: ${res.error}`);
    }
  };

  // Reset Filters
  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedRound('All');
    setDifficultyFilter('All');
    setStatusFilter('All');
    setCompanyFilter('All');
    setTopicFilter('All');
    setSortBy('recent');
    setSortOrder('desc');
  };

  const isFiltered =
    searchQuery ||
    selectedRound !== 'All' ||
    difficultyFilter !== 'All' ||
    statusFilter !== 'All' ||
    companyFilter !== 'All' ||
    topicFilter !== 'All' ||
    sortBy !== 'recent';

  return (
    <div className="fade-in">
      {/* Page Header */}
      <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
        <div>
          <h1 className="section-title">Interview Memory Bank</h1>
          <p className="section-desc">
            Record actual technical and HR interview questions, log your answers, and refine them for future recruitment rounds.
          </p>
        </div>
        <button
          type="button"
          className="btn-primary"
          onClick={() => {
            setEditingQuestion(null);
            setIsModalOpen(true);
          }}
        >
          <Plus size={16} />
          <span>Record Question</span>
        </button>
      </div>

      {/* Summary Preparation Stats Bar */}
      <div className="questions-stats-grid">
        <div className="q-stat-card">
          <div className="q-stat-icon" style={{ background: 'var(--primary-light)', color: 'var(--primary)' }}>
            <HelpCircle size={22} />
          </div>
          <div className="q-stat-info">
            <span className="q-stat-value">{stats.total}</span>
            <span className="q-stat-label">Total Saved Questions</span>
          </div>
        </div>

        <div className="q-stat-card">
          <div className="q-stat-icon" style={{ background: '#f0f9ff', color: '#0284c7' }}>
            <Code size={22} />
          </div>
          <div className="q-stat-info">
            <span className="q-stat-value">{stats.technical}</span>
            <span className="q-stat-label">Technical Questions</span>
          </div>
        </div>

        <div className="q-stat-card">
          <div className="q-stat-icon" style={{ background: '#faf5ff', color: '#9333ea' }}>
            <Users size={22} />
          </div>
          <div className="q-stat-info">
            <span className="q-stat-value">{stats.hr_behavioral}</span>
            <span className="q-stat-label">HR & Behavioral</span>
          </div>
        </div>

        <div className="q-stat-card">
          <div className="q-stat-icon" style={{ background: '#ecfdf5', color: '#10b981' }}>
            <CheckCircle2 size={22} />
          </div>
          <div className="q-stat-info">
            <span className="q-stat-value">{stats.confident}</span>
            <span className="q-stat-label">Marked Confident</span>
          </div>
        </div>

        <div className="q-stat-card">
          <div className="q-stat-icon" style={{ background: '#fffbeb', color: '#f59e0b' }}>
            <Clock size={22} />
          </div>
          <div className="q-stat-info">
            <span className="q-stat-value">{stats.needs_review}</span>
            <span className="q-stat-label">Needs Review</span>
          </div>
        </div>
      </div>

      {/* Round Types Navigation Strip */}
      <div className="round-nav-strip">
        {ROUND_TABS.map((tab) => {
          const count =
            tab.id === 'All'
              ? stats.total
              : stats.by_round?.[tab.id] || 0;
          return (
            <button
              key={tab.id}
              type="button"
              className={`round-tab-btn ${selectedRound === tab.id ? 'active' : ''}`}
              onClick={() => setSelectedRound(tab.id)}
            >
              <span>{tab.label}</span>
              <span className="round-tab-count">{count}</span>
            </button>
          );
        })}
      </div>

      {/* Controls Card (Search + Multi-Filter + Sort) */}
      <div className="questions-controls-card">
        <div className="questions-search-row">
          <div className="q-search-box">
            <Search size={16} className="q-search-icon" />
            <input
              type="text"
              className="q-search-input"
              placeholder="Search question text, topic, company, role, or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="q-filters-row">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            <Filter size={14} />
            <span>Filter:</span>
          </div>

          {/* Difficulty Filter */}
          <select
            className="q-select-filter"
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
          >
            <option value="All">All Difficulties</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>

          {/* Status Filter */}
          <select
            className="q-select-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All">All Statuses</option>
            <option value="New">🟡 New</option>
            <option value="Learning">🟠 Learning</option>
            <option value="Confident">🟢 Confident</option>
          </select>

          {/* Company Filter */}
          {availableCompanies.length > 0 && (
            <select
              className="q-select-filter"
              value={companyFilter}
              onChange={(e) => setCompanyFilter(e.target.value)}
            >
              <option value="All">All Companies</option>
              {availableCompanies.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          )}

          {/* Topic Filter */}
          {availableTopics.length > 0 && (
            <select
              className="q-select-filter"
              value={topicFilter}
              onChange={(e) => setTopicFilter(e.target.value)}
            >
              <option value="All">All Topics</option>
              {availableTopics.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          )}

          {/* Sort Control */}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <ArrowUpDown size={14} style={{ color: 'var(--text-muted)' }} />
            <select
              className="q-select-filter"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="recent">Recently Added</option>
              <option value="interview_date">Interview Date</option>
              <option value="difficulty">Difficulty</option>
              <option value="company">Company</option>
            </select>
          </div>

          {isFiltered && (
            <button type="button" className="q-clear-btn" onClick={handleResetFilters}>
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="alert-banner alert-danger" style={{ marginBottom: '1.5rem' }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3.5rem 0', color: 'var(--text-muted)' }}>
          <div className="loading-spinner" style={{ margin: '0 auto 1rem' }} />
          <p style={{ fontSize: '0.95rem' }}>Loading interview questions...</p>
        </div>
      ) : questions.length === 0 ? (
        /* Empty State */
        <div
          className="empty-state-card"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-card)',
            borderRadius: 'var(--radius-lg)',
            padding: '3.5rem 2rem',
            textAlign: 'center'
          }}
        >
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'var(--primary-light)',
              color: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem'
            }}
          >
            <HelpCircle size={28} />
          </div>
          <h3 style={{ fontSize: '1.25rem', color: 'var(--text-main)', margin: '0 0 0.5rem' }}>
            {isFiltered ? 'No Questions Match Your Filters' : 'No Interview Questions Saved Yet'}
          </h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto 1.5rem', lineHeight: 1.5 }}>
            {isFiltered
              ? 'Try adjusting your search keywords, clearing company or difficulty filters, or switching round categories.'
              : 'Start logging actual questions you were asked during campus placements, online tests, and screening calls to build your permanent interview memory bank.'}
          </p>
          {isFiltered ? (
            <button type="button" className="btn-secondary" onClick={handleResetFilters}>
              Clear All Filters
            </button>
          ) : (
            <button
              type="button"
              className="btn-primary"
              onClick={() => {
                setEditingQuestion(null);
                setIsModalOpen(true);
              }}
            >
              <Plus size={16} />
              <span>Record Your First Question</span>
            </button>
          )}
        </div>
      ) : (
        /* Questions Grid */
        <div className="questions-grid">
          {questions.map((q) => {
            const roundBadgeClass = `badge-round-${(q.round_type || 'technical').toLowerCase().replace(/\s+/g, '-')}`;
            const diffBadgeClass = `badge-diff-${(q.difficulty || 'intermediate').toLowerCase()}`;
            const statusBadgeClass = `badge-status-${(q.review_status || 'new').toLowerCase()}`;

            const tags = q.tags ? q.tags.split(',').map((t) => t.trim()).filter(Boolean) : [];

            return (
              <div key={q.id} className="question-card">
                <div>
                  {/* Card Header & Badges */}
                  <div className="q-card-header">
                    <div className="q-card-badges">
                      <span className={`q-badge ${roundBadgeClass}`}>
                        {q.round_type}
                      </span>
                      <span className={`q-badge ${diffBadgeClass}`}>
                        {q.difficulty}
                      </span>
                    </div>

                    {/* Quick status toggle dropdown */}
                    <select
                      className={`quick-status-selector ${statusBadgeClass}`}
                      value={q.review_status || 'New'}
                      onChange={(e) => handleQuickStatusChange(q.id, e.target.value)}
                      title="Change review mastery status"
                    >
                      <option value="New">🟡 New</option>
                      <option value="Learning">🟠 Learning</option>
                      <option value="Confident">🟢 Confident</option>
                    </select>
                  </div>

                  {/* Company & Role / Topic */}
                  {(q.company_name || q.topic) && (
                    <div className="q-card-company-line">
                      {q.company_name && (
                        <span className="q-company-pill">
                          <Building size={13} />
                          <span>{q.company_name}</span>
                          {q.job_role && <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>({q.job_role})</span>}
                        </span>
                      )}
                      {q.topic && (
                        <span className="q-topic-pill">
                          {q.topic}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Question Text */}
                  <h3
                    className="q-card-title"
                    onClick={() => setDetailQuestion(q)}
                    title="Click to view full answer and reflection"
                  >
                    {q.question_text}
                  </h3>

                  {/* Answer Preview Box */}
                  {(q.original_answer || q.personal_answer || q.expected_answer) && (
                    <div className="q-answer-preview-box" onClick={() => setDetailQuestion(q)} style={{ cursor: 'pointer' }}>
                      <div className="q-answer-preview-title">
                        <BookOpen size={12} />
                        <span>
                          {q.original_answer || q.personal_answer ? 'My Response Notes' : 'Expected Points'}
                        </span>
                      </div>
                      <p className="q-answer-preview-text">
                        {q.original_answer || q.personal_answer || q.expected_answer}
                      </p>
                    </div>
                  )}

                  {/* Tags */}
                  {tags.length > 0 && (
                    <div className="q-tags-container">
                      {tags.slice(0, 4).map((tag, idx) => (
                        <span key={idx} className="q-tag-pill">
                          #{tag}
                        </span>
                      ))}
                      {tags.length > 4 && (
                        <span className="q-tag-pill" style={{ color: 'var(--primary)' }}>
                          +{tags.length - 4} more
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Footer with date & actions */}
                <div className="q-card-footer">
                  <span className="q-card-date">
                    <Calendar size={12} />
                    <span>{q.interview_date || 'Encountered in interview'}</span>
                  </span>

                  <div className="q-card-actions">
                    <button
                      type="button"
                      className="q-action-icon-btn"
                      onClick={() =>
                        navigate(
                          `/practice?round_type=${encodeURIComponent(
                            q.round_type || 'Technical'
                          )}${q.job_id ? `&job_id=${q.job_id}` : ''}`
                        )
                      }
                      title="Practice this question in Mock Interview Studio"
                    >
                      <Mic size={14} />
                    </button>
                    <button
                      type="button"
                      className="q-action-icon-btn"
                      onClick={() => setDetailQuestion(q)}
                      title="View full answer & improvement notes"
                    >
                      <BookOpen size={14} />
                    </button>
                    <button
                      type="button"
                      className="q-action-icon-btn"
                      onClick={() => {
                        setEditingQuestion(q);
                        setIsModalOpen(true);
                      }}
                      title="Edit question"
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      type="button"
                      className="q-action-icon-btn danger"
                      onClick={() => setDeletingQuestion(q)}
                      title="Delete question"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add / Edit Question Modal */}
      <QuestionModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingQuestion(null);
        }}
        onSave={handleSaveQuestion}
        initialQuestion={editingQuestion}
        savedJobs={savedJobs}
      />

      {/* Question Details Modal */}
      <QuestionDetailModal
        isOpen={!!detailQuestion}
        onClose={() => setDetailQuestion(null)}
        question={detailQuestion}
        onEdit={(q) => {
          setEditingQuestion(q);
          setIsModalOpen(true);
        }}
        onDelete={(q) => setDeletingQuestion(q)}
        onStatusChange={handleQuickStatusChange}
        onNavigateToJob={(jobId) => {
          setDetailQuestion(null);
          navigate(`/applications?highlight=${jobId}`);
        }}
      />

      {/* Delete Confirmation Modal */}
      {deletingQuestion && (
        <div className="modal-overlay" onClick={() => setDeletingQuestion(null)}>
          <div className="modal-card" style={{ maxWidth: '440px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: '#fee2e2',
                    color: '#dc2626',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <AlertTriangle size={18} />
                </div>
                <h2 style={{ fontSize: '1.15rem' }}>Delete Interview Question</h2>
              </div>
              <button
                className="modal-close-btn"
                onClick={() => setDeletingQuestion(null)}
                aria-label="Close modal"
              >
                <AlertTriangle size={18} />
              </button>
            </div>

            <div className="modal-body">
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Are you sure you want to permanently delete this question?
              </p>
              <div
                style={{
                  background: 'var(--bg-app)',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  margin: '0.75rem 0',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: 'var(--text-main)',
                  borderLeft: '3px solid #ef4444'
                }}
              >
                "{deletingQuestion.question_text}"
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                This action cannot be undone and will permanently remove your recorded answer and reflection notes.
              </p>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setDeletingQuestion(null)}
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-danger"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete Question'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
