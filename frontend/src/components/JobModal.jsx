import React, { useState, useEffect } from 'react';
import { X, AlertCircle } from 'lucide-react';
import { createApplication, updateApplication } from '../services/api';

const STATUS_OPTIONS = [
  'Saved',
  'Applied',
  'Assessment',
  'Interview',
  'Offer',
  'Rejected',
  'Withdrawn'
];

const WORK_MODE_OPTIONS = ['', 'On-site', 'Hybrid', 'Remote'];
const EMPLOYMENT_TYPE_OPTIONS = ['', 'Internship', 'Full-time', 'Part-time'];

export default function JobModal({ isOpen, onClose, onJobSaved, initialJob = null }) {
  const isEditing = Boolean(initialJob);

  const [formData, setFormData] = useState({
    company_name: '',
    job_title: '',
    application_status: 'Saved',
    location: '',
    work_mode: '',
    employment_type: '',
    skills: '',
    deadline: '',
    application_date: '',
    job_url: '',
    company_url: '',
    job_description: '',
    notes: ''
  });

  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState(null);

  useEffect(() => {
    if (initialJob) {
      setFormData({
        company_name: initialJob.company_name || '',
        job_title: initialJob.job_title || '',
        application_status: initialJob.application_status || 'Saved',
        location: initialJob.location || '',
        work_mode: initialJob.work_mode || '',
        employment_type: initialJob.employment_type || '',
        skills: initialJob.skills || '',
        deadline: initialJob.deadline || '',
        application_date: initialJob.application_date || '',
        job_url: initialJob.job_url || '',
        company_url: initialJob.company_url || '',
        job_description: initialJob.job_description || '',
        notes: initialJob.notes || ''
      });
    } else {
      setFormData({
        company_name: '',
        job_title: '',
        application_status: 'Saved',
        location: '',
        work_mode: '',
        employment_type: '',
        skills: '',
        deadline: '',
        application_date: '',
        job_url: '',
        company_url: '',
        job_description: '',
        notes: ''
      });
    }
    setErrors({});
    setServerError(null);
  }, [initialJob, isOpen]);

  if (!isOpen) return null;

  const validate = () => {
    const newErrors = {};
    if (!formData.company_name.trim()) {
      newErrors.company_name = 'Company name is required';
    }
    if (!formData.job_title.trim()) {
      newErrors.job_title = 'Job role / designation is required';
    }
    if (!formData.application_status) {
      newErrors.application_status = 'Application status is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    setServerError(null);

    // Prepare payload (convert empty strings to null for optional database fields)
    const payload = {
      ...formData,
      company_name: formData.company_name.trim(),
      job_title: formData.job_title.trim(),
      location: formData.location.trim() || null,
      work_mode: formData.work_mode || null,
      employment_type: formData.employment_type || null,
      skills: formData.skills.trim() || null,
      deadline: formData.deadline || null,
      application_date: formData.application_date || null,
      job_url: formData.job_url.trim() || null,
      company_url: formData.company_url.trim() || null,
      job_description: formData.job_description.trim() || null,
      notes: formData.notes.trim() || null
    };

    let res;
    if (isEditing) {
      res = await updateApplication(initialJob.id, payload);
    } else {
      res = await createApplication(payload);
    }

    setSubmitting(false);

    if (res.ok) {
      onJobSaved(res.data, isEditing);
      onClose();
    } else {
      setServerError(res.error || 'Failed to save job application.');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{isEditing ? 'Edit Job Opportunity' : 'Save New Job Opportunity'}</h2>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {serverError && (
              <div
                style={{
                  background: '#fee2e2',
                  border: '1px solid #fecaca',
                  color: '#991b1b',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.825rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                <AlertCircle size={16} />
                <span>{serverError}</span>
              </div>
            )}

            {/* Section 1: Core Required Fields */}
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="company_name">
                  Company Name <span className="required">*</span>
                </label>
                <input
                  id="company_name"
                  type="text"
                  name="company_name"
                  className={`form-input ${errors.company_name ? 'error' : ''}`}
                  placeholder="e.g. Google, Microsoft, Stripe"
                  value={formData.company_name}
                  onChange={handleChange}
                  autoFocus
                />
                {errors.company_name && <span className="field-error">{errors.company_name}</span>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="job_title">
                  Job Role / Designation <span className="required">*</span>
                </label>
                <input
                  id="job_title"
                  type="text"
                  name="job_title"
                  className={`form-input ${errors.job_title ? 'error' : ''}`}
                  placeholder="e.g. Software Engineer Intern"
                  value={formData.job_title}
                  onChange={handleChange}
                />
                {errors.job_title && <span className="field-error">{errors.job_title}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="application_status">
                  Application Status <span className="required">*</span>
                </label>
                <select
                  id="application_status"
                  name="application_status"
                  className="form-select"
                  value={formData.application_status}
                  onChange={handleChange}
                >
                  {STATUS_OPTIONS.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="location">
                  Location
                </label>
                <input
                  id="location"
                  type="text"
                  name="location"
                  className="form-input"
                  placeholder="e.g. San Francisco, CA or Remote"
                  value={formData.location}
                  onChange={handleChange}
                />
              </div>
            </div>

            {/* Section 2: Work Mode & Dates */}
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="work_mode">
                  Work Mode
                </label>
                <select
                  id="work_mode"
                  name="work_mode"
                  className="form-select"
                  value={formData.work_mode}
                  onChange={handleChange}
                >
                  <option value="">Select Work Mode...</option>
                  {WORK_MODE_OPTIONS.filter(Boolean).map((wm) => (
                    <option key={wm} value={wm}>
                      {wm}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="employment_type">
                  Employment Type
                </label>
                <select
                  id="employment_type"
                  name="employment_type"
                  className="form-select"
                  value={formData.employment_type}
                  onChange={handleChange}
                >
                  <option value="">Select Employment Type...</option>
                  {EMPLOYMENT_TYPE_OPTIONS.filter(Boolean).map((et) => (
                    <option key={et} value={et}>
                      {et}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="deadline">
                  Application Deadline
                </label>
                <input
                  id="deadline"
                  type="date"
                  name="deadline"
                  className="form-input"
                  value={formData.deadline}
                  onChange={handleChange}
                />
                <span className="form-hint">SkillBridge will highlight approaching dates.</span>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="application_date">
                  Date Applied
                </label>
                <input
                  id="application_date"
                  type="date"
                  name="application_date"
                  className="form-input"
                  value={formData.application_date}
                  onChange={handleChange}
                />
              </div>
            </div>

            {/* Section 3: Skills & URLs */}
            <div className="form-group full-width">
              <label className="form-label" htmlFor="skills">
                Required Skills
              </label>
              <input
                id="skills"
                type="text"
                name="skills"
                className="form-input"
                placeholder="e.g. Python, React, SQL, AWS, REST APIs"
                value={formData.skills}
                onChange={handleChange}
              />
              <span className="form-hint">Separate key skills with commas for quick tag rendering.</span>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="job_url">
                  Job Posting URL
                </label>
                <input
                  id="job_url"
                  type="url"
                  name="job_url"
                  className="form-input"
                  placeholder="https://company.com/jobs/123"
                  value={formData.job_url}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="company_url">
                  Company Careers URL
                </label>
                <input
                  id="company_url"
                  type="url"
                  name="company_url"
                  className="form-input"
                  placeholder="https://company.com/careers"
                  value={formData.company_url}
                  onChange={handleChange}
                />
              </div>
            </div>

            {/* Section 4: Description & Notes */}
            <div className="form-group full-width">
              <label className="form-label" htmlFor="job_description">
                Job Description
              </label>
              <textarea
                id="job_description"
                name="job_description"
                rows="3"
                className="form-textarea"
                placeholder="Paste key responsibilities or requirements..."
                value={formData.job_description}
                onChange={handleChange}
              />
            </div>

            <div className="form-group full-width">
              <label className="form-label" htmlFor="notes">
                Personal Notes
              </label>
              <textarea
                id="notes"
                name="notes"
                rows="2"
                className="form-textarea"
                placeholder="e.g. Reached out to alumnus on LinkedIn; interview scheduled for next week..."
                value={formData.notes}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : isEditing ? 'Update Job' : 'Save Opportunity'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
