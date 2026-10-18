import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Plus,
  Search,
  X,
  LayoutGrid,
  Table as TableIcon,
  Building2,
  Calendar,
  Clock,
  MapPin,
  ExternalLink,
  Edit2,
  Trash2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Briefcase,
  ArrowUpDown,
  FileSearch,
  Mic,
  HelpCircle
} from 'lucide-react';
import {
  getApplications,
  updateApplicationStatus,
  deleteApplication
} from '../services/api';
import JobModal from '../components/JobModal';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import '../styles/applications.css';

const STATUS_LIST = [
  'All',
  'Saved',
  'Applied',
  'Assessment',
  'Interview',
  'Offer',
  'Rejected',
  'Withdrawn'
];

const WORK_MODE_LIST = ['All', 'On-site', 'Hybrid', 'Remote'];
const EMPLOYMENT_TYPE_LIST = ['All', 'Internship', 'Full-time', 'Part-time'];

const STATUS_CLASS_MAP = {
  Saved: 'status-saved',
  Applied: 'status-applied',
  Assessment: 'status-assessment',
  Interview: 'status-interview',
  Interviewing: 'status-interview',
  Offer: 'status-offer',
  Rejected: 'status-rejected',
  Withdrawn: 'status-withdrawn'
};

export default function Applications() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Search
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || 'All');
  const [workModeFilter, setWorkModeFilter] = useState('All');
  const [empTypeFilter, setEmpTypeFilter] = useState('All');
  const [sortBy, setSortBy] = useState('recent');
  const [sortOrder, setSortOrder] = useState('desc');

  // View state: 'grid' or 'table'
  const [viewMode, setViewMode] = useState('grid');

  // Modals state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [deletingJob, setDeletingJob] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Expandable details cards
  const [expandedCardId, setExpandedCardId] = useState(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await getApplications({
      search,
      status: statusFilter,
      work_mode: workModeFilter,
      employment_type: empTypeFilter,
      sort_by: sortBy,
      sort_order: sortOrder
    });

    if (res.ok) {
      setJobs(res.data || []);
    } else {
      setError(res.error || 'Failed to load applications.');
    }
    setLoading(false);
  }, [search, statusFilter, workModeFilter, empTypeFilter, sortBy, sortOrder]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Handle Quick Status Change
  const handleStatusChange = async (jobId, newStatus) => {
    const res = await updateApplicationStatus(jobId, newStatus);
    if (res.ok) {
      setJobs((prev) =>
        prev.map((job) =>
          job.id === jobId ? { ...job, application_status: newStatus } : job
        )
      );
    } else {
      alert(`Could not update status: ${res.error}`);
    }
  };

  // Open Edit Modal
  const handleEdit = (job) => {
    setEditingJob(job);
    setIsModalOpen(true);
  };

  // Handle Save Callback
  const handleJobSaved = (savedJob, isEdit) => {
    if (isEdit) {
      setJobs((prev) => prev.map((j) => (j.id === savedJob.id ? savedJob : j)));
    } else {
      setJobs((prev) => [savedJob, ...prev]);
    }
    // Refresh to respect current sort & filters
    fetchJobs();
  };

  // Confirm Delete
  const handleConfirmDelete = async () => {
    if (!deletingJob) return;
    setIsDeleting(true);
    const res = await deleteApplication(deletingJob.id);
    setIsDeleting(false);
    if (res.ok) {
      setJobs((prev) => prev.filter((j) => j.id !== deletingJob.id));
      setDeletingJob(null);
    } else {
      alert(`Delete failed: ${res.error}`);
    }
  };

  // Reset all filters
  const handleResetFilters = () => {
    setSearch('');
    setStatusFilter('All');
    setWorkModeFilter('All');
    setEmpTypeFilter('All');
    setSortBy('recent');
    setSortOrder('desc');
  };

  // Approaching Deadlines Checker
  const approachingDeadlines = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const inSevenDays = new Date();
    inSevenDays.setDate(today.getDate() + 7);

    return jobs.filter((job) => {
      if (!job.deadline) return false;
      if (['Rejected', 'Withdrawn'].includes(job.application_status)) return false;
      const d = new Date(job.deadline);
      return d >= today && d <= inSevenDays;
    });
  }, [jobs]);

  // Helper for deadline badge display
  const getDeadlineMeta = (deadlineStr) => {
    if (!deadlineStr) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const deadline = new Date(deadlineStr);
    const diffTime = deadline.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { label: `Deadline Passed (${Math.abs(diffDays)}d ago)`, isUrgent: true };
    }
    if (diffDays === 0) {
      return { label: 'Deadline Today!', isUrgent: true };
    }
    if (diffDays <= 3) {
      return { label: `Deadline in ${diffDays} day${diffDays > 1 ? 's' : ''}`, isUrgent: true };
    }
    if (diffDays <= 7) {
      return { label: `Deadline in ${diffDays} days`, isUrgent: false };
    }
    return { label: `Deadline: ${deadlineStr}`, isUrgent: false };
  };

  return (
    <div className="tracker-page fade-in">
      {/* 1. Header with Title & Action */}
      <div className="tracker-header">
        <div className="tracker-header-left">
          <h1>
            <span>Job Application Tracker</span>
            <span className="count-pill">{jobs.length} Opportunities</span>
          </h1>
          <p>
            Organize applications, track interview progression, and manage recruitment deadlines.
          </p>
        </div>

        <button
          className="btn-primary"
          onClick={() => {
            setEditingJob(null);
            setIsModalOpen(true);
          }}
        >
          <Plus size={18} />
          <span>Save New Job</span>
        </button>
      </div>

      {/* 2. Approaching Deadline Alert Callout */}
      {approachingDeadlines.length > 0 && (
        <div className="deadline-alert-banner">
          <div className="deadline-alert-content">
            <AlertTriangle size={20} className="deadline-alert-icon" />
            <div>
              <strong>
                {approachingDeadlines.length} Upcoming Application Deadline
                {approachingDeadlines.length > 1 ? 's' : ''}!
              </strong>
              <div>
                Applications for{' '}
                {approachingDeadlines.map((j) => `${j.company_name} (${j.job_title})`).join(', ')}{' '}
                are approaching within 7 days.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. Search and Filters Toolbar */}
      <div className="filter-toolbar">
        <div className="toolbar-top">
          {/* Search Box */}
          <div className="search-box">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by company name, job role, or skill..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button
                className="search-clear-btn"
                onClick={() => setSearch('')}
                aria-label="Clear search"
              >
                <X size={16} />
              </button>
            )}
          </div>

          {/* View Mode Toggle */}
          <div className="view-toggle-group">
            <button
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="Card Grid View"
            >
              <LayoutGrid size={16} />
              <span>Cards</span>
            </button>
            <button
              className={`view-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
              title="Table View"
            >
              <TableIcon size={16} />
              <span>Table</span>
            </button>
          </div>
        </div>

        {/* Filter Dropdowns */}
        <div className="toolbar-filters">
          {/* Status Filter */}
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter by Status"
          >
            {STATUS_LIST.map((st) => (
              <option key={st} value={st}>
                Status: {st}
              </option>
            ))}
          </select>

          {/* Work Mode Filter */}
          <select
            className="filter-select"
            value={workModeFilter}
            onChange={(e) => setWorkModeFilter(e.target.value)}
            aria-label="Filter by Work Mode"
          >
            {WORK_MODE_LIST.map((wm) => (
              <option key={wm} value={wm}>
                Work Mode: {wm}
              </option>
            ))}
          </select>

          {/* Employment Type Filter */}
          <select
            className="filter-select"
            value={empTypeFilter}
            onChange={(e) => setEmpTypeFilter(e.target.value)}
            aria-label="Filter by Employment Type"
          >
            {EMPLOYMENT_TYPE_LIST.map((et) => (
              <option key={et} value={et}>
                Type: {et}
              </option>
            ))}
          </select>

          {/* Sort By */}
          <select
            className="filter-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            aria-label="Sort by"
          >
            <option value="recent">Sort: Recently Added</option>
            <option value="deadline">Sort: Application Deadline</option>
            <option value="company">Sort: Company Name</option>
          </select>

          {/* Sort Direction Toggle */}
          <button
            className="filter-select"
            style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}
            onClick={() => setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))}
            title={`Toggle order: currently ${sortOrder.toUpperCase()}`}
          >
            <ArrowUpDown size={14} />
            <span>{sortOrder === 'asc' ? 'Ascending' : 'Descending'}</span>
          </button>

          {(search || statusFilter !== 'All' || workModeFilter !== 'All' || empTypeFilter !== 'All') && (
            <button className="reset-filters-btn" onClick={handleResetFilters}>
              Reset filters
            </button>
          )}
        </div>
      </div>

      {/* 4. Content Area: Loading, Error, Empty, or Cards/Table */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading saved applications...
        </div>
      ) : error ? (
        <div
          style={{
            background: '#fee2e2',
            color: '#991b1b',
            padding: '1.5rem',
            borderRadius: 'var(--radius-lg)',
            textAlign: 'center'
          }}
        >
          {error}
        </div>
      ) : jobs.length === 0 ? (
        <div className="empty-state-box">
          <div className="empty-icon-circle">
            <Briefcase size={28} />
          </div>
          <h3>
            {search || statusFilter !== 'All' || workModeFilter !== 'All' || empTypeFilter !== 'All'
              ? 'No matching jobs found'
              : 'No job applications saved yet'}
          </h3>
          <p>
            {search || statusFilter !== 'All' || workModeFilter !== 'All' || empTypeFilter !== 'All'
              ? 'Try adjusting your search keywords or resetting your active filters.'
              : 'Start tracking your internships, new grad opportunities, and job leads in one organized place.'}
          </p>
          {search || statusFilter !== 'All' || workModeFilter !== 'All' || empTypeFilter !== 'All' ? (
            <button className="btn-secondary" onClick={handleResetFilters}>
              Reset Filters
            </button>
          ) : (
            <button
              className="btn-primary"
              onClick={() => {
                setEditingJob(null);
                setIsModalOpen(true);
              }}
            >
              <Plus size={18} />
              <span>Save Your First Job</span>
            </button>
          )}
        </div>
      ) : viewMode === 'grid' ? (
        /* Card Grid View */
        <div className="job-cards-grid">
          {jobs.map((job) => {
            const deadlineMeta = getDeadlineMeta(job.deadline);
            const isExpanded = expandedCardId === job.id;
            const skillsList = job.skills
              ? job.skills.split(',').map((s) => s.trim()).filter(Boolean)
              : [];

            return (
              <div key={job.id} className="job-card">
                {/* Header: Company & Title */}
                <div className="job-card-header">
                  <div className="job-card-title">
                    <h3>{job.job_title}</h3>
                    <div className="company-name">
                      <Building2 size={16} />
                      <span>{job.company_name}</span>
                    </div>
                  </div>
                  <span
                    className={`status-badge ${
                      STATUS_CLASS_MAP[job.application_status] || 'status-saved'
                    }`}
                  >
                    {job.application_status}
                  </span>
                </div>

                {/* Metadata Row */}
                <div className="job-meta-row">
                  {job.location && (
                    <span className="meta-chip">
                      <MapPin size={12} />
                      <span>{job.location}</span>
                    </span>
                  )}
                  {job.work_mode && (
                    <span className="meta-chip">
                      <span>{job.work_mode}</span>
                    </span>
                  )}
                  {job.employment_type && (
                    <span className="meta-chip">
                      <Clock size={12} />
                      <span>{job.employment_type}</span>
                    </span>
                  )}
                  {deadlineMeta && (
                    <span
                      className={`meta-chip deadline-chip ${
                        deadlineMeta.isUrgent ? 'urgent' : ''
                      }`}
                    >
                      <Calendar size={12} />
                      <span>{deadlineMeta.label}</span>
                    </span>
                  )}
                </div>

                {/* Skills Chips */}
                {skillsList.length > 0 && (
                  <div className="job-skills-container">
                    {skillsList.slice(0, 4).map((skill, idx) => (
                      <span key={idx} className="skill-tag">
                        {skill}
                      </span>
                    ))}
                    {skillsList.length > 4 && (
                      <span className="skill-tag" style={{ color: 'var(--text-muted)' }}>
                        +{skillsList.length - 4} more
                      </span>
                    )}
                  </div>
                )}

                {/* Quick Status Dropdown */}
                <div className="quick-status-wrapper">
                  <span className="quick-status-label">Stage:</span>
                  <select
                    className="quick-status-select"
                    value={job.application_status}
                    onChange={(e) => handleStatusChange(job.id, e.target.value)}
                  >
                    {STATUS_LIST.filter((s) => s !== 'All').map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Expandable Details Drawer */}
                {isExpanded && (
                  <div className="card-details-drawer">
                    {job.application_date && (
                      <div>
                        <span className="details-label">Date Applied: </span>
                        <span>{job.application_date}</span>
                      </div>
                    )}
                    {job.job_description && (
                      <div>
                        <span className="details-label">Description: </span>
                        <p style={{ marginTop: '0.2rem' }}>{job.job_description}</p>
                      </div>
                    )}
                    {job.notes && (
                      <div>
                        <span className="details-label">Personal Notes: </span>
                        <p style={{ marginTop: '0.2rem', fontStyle: 'italic' }}>{job.notes}</p>
                      </div>
                    )}
                    {skillsList.length > 4 && (
                      <div>
                        <span className="details-label">All Required Skills: </span>
                        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginTop: '0.3rem' }}>
                          {skillsList.map((skill, idx) => (
                            <span key={idx} className="skill-tag">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Card Footer */}
                <div className="job-card-footer">
                  <div className="card-links">
                    {job.job_url && (
                      <a
                        href={job.job_url}
                        target="_blank"
                        rel="noreferrer"
                        className="card-link-btn"
                        title="Open Job Posting"
                      >
                        <ExternalLink size={13} />
                        <span>Job Post</span>
                      </a>
                    )}
                    {job.company_url && (
                      <a
                        href={job.company_url}
                        target="_blank"
                        rel="noreferrer"
                        className="card-link-btn"
                        title="Open Careers Portal"
                      >
                        <ExternalLink size={13} />
                        <span>Careers</span>
                      </a>
                    )}
                    {(job.job_description || job.notes || skillsList.length > 4 || job.application_date) && (
                      <button
                        className="card-link-btn"
                        onClick={() =>
                          setExpandedCardId((prev) => (prev === job.id ? null : job.id))
                        }
                      >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        <span>{isExpanded ? 'Less' : 'Details'}</span>
                      </button>
                    )}
                  </div>

                  <div className="card-actions">
                    <button
                      className="action-icon-btn"
                      onClick={() => navigate(`/job-analyzer?job_id=${job.id}`)}
                      title="Analyze Job Description"
                      style={{ color: 'var(--primary)' }}
                    >
                      <FileSearch size={15} />
                    </button>
                    <button
                      className="action-icon-btn"
                      onClick={() => navigate(`/practice?job_id=${job.id}`)}
                      title="Start Mock Interview for this Job"
                      style={{ color: '#2563eb' }}
                    >
                      <Mic size={15} />
                    </button>
                    <button
                      className="action-icon-btn"
                      onClick={() => navigate(`/questions?job_id=${job.id}`)}
                      title="View Questions for this Job"
                      style={{ color: '#7c3aed' }}
                    >
                      <HelpCircle size={15} />
                    </button>
                    <button
                      className="action-icon-btn"
                      onClick={() => handleEdit(job)}
                      title="Edit Opportunity"
                    >
                      <Edit2 size={15} />
                    </button>
                    <button
                      className="action-icon-btn delete"
                      onClick={() => setDeletingJob(job)}
                      title="Delete Opportunity"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Table View */
        <div className="table-container">
          <table className="apps-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Role / Designation</th>
                <th>Status</th>
                <th>Work Mode</th>
                <th>Type</th>
                <th>Deadline</th>
                <th>Links</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => {
                const deadlineMeta = getDeadlineMeta(job.deadline);
                return (
                  <tr key={job.id}>
                    <td>
                      <strong style={{ color: 'var(--text-main)' }}>{job.company_name}</strong>
                      {job.location && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {job.location}
                        </div>
                      )}
                    </td>
                    <td>{job.job_title}</td>
                    <td>
                      <select
                        className="quick-status-select"
                        value={job.application_status}
                        onChange={(e) => handleStatusChange(job.id, e.target.value)}
                      >
                        {STATUS_LIST.filter((s) => s !== 'All').map((st) => (
                          <option key={st} value={st}>
                            {st}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>{job.work_mode || '—'}</td>
                    <td>{job.employment_type || '—'}</td>
                    <td>
                      {deadlineMeta ? (
                        <span
                          className={`meta-chip deadline-chip ${
                            deadlineMeta.isUrgent ? 'urgent' : ''
                          }`}
                        >
                          {deadlineMeta.label}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        {job.job_url && (
                          <a
                            href={job.job_url}
                            target="_blank"
                            rel="noreferrer"
                            className="card-link-btn"
                            title="Open Job Posting"
                          >
                            <ExternalLink size={14} />
                          </a>
                        )}
                        {job.company_url && (
                          <a
                            href={job.company_url}
                            target="_blank"
                            rel="noreferrer"
                            className="card-link-btn"
                            title="Open Careers Portal"
                          >
                            <Building2 size={14} />
                          </a>
                        )}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.3rem', justifyContent: 'flex-end' }}>
                        <button
                          className="action-icon-btn"
                          onClick={() => navigate(`/job-analyzer?job_id=${job.id}`)}
                          title="Analyze Job Description"
                          style={{ color: 'var(--primary)' }}
                        >
                          <FileSearch size={15} />
                        </button>
                        <button
                          className="action-icon-btn"
                          onClick={() => navigate(`/practice?job_id=${job.id}`)}
                          title="Start Mock Interview for this Job"
                          style={{ color: '#2563eb' }}
                        >
                          <Mic size={15} />
                        </button>
                        <button
                          className="action-icon-btn"
                          onClick={() => navigate(`/questions?job_id=${job.id}`)}
                          title="View Questions for this Job"
                          style={{ color: '#7c3aed' }}
                        >
                          <HelpCircle size={15} />
                        </button>
                        <button
                          className="action-icon-btn"
                          onClick={() => handleEdit(job)}
                          title="Edit"
                        >
                          <Edit2 size={15} />
                        </button>
                        <button
                          className="action-icon-btn delete"
                          onClick={() => setDeletingJob(job)}
                          title="Delete"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* 5. Add / Edit Modal */}
      <JobModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingJob(null);
        }}
        onJobSaved={handleJobSaved}
        initialJob={editingJob}
      />

      {/* 6. Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={Boolean(deletingJob)}
        onClose={() => setDeletingJob(null)}
        onConfirm={handleConfirmDelete}
        job={deletingJob}
        deleting={isDeleting}
      />
    </div>
  );
}
