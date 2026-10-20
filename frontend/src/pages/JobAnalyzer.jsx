import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  FileSearch,
  Sparkles,
  History,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Briefcase,
  Layers,
  ArrowRight,
  Trash2,
  BookOpen,
  GraduationCap,
  HelpCircle,
  Mic
} from 'lucide-react';
import {
  analyzeJob,
  getAnalysisHistory,
  getAnalysisById,
  deleteAnalysis,
  getApplications,
  getApplicationById
} from '../services/api';
import '../styles/analyzer.css';

const SAMPLE_PROFILES = {
  frontend:
    'Proficient in JavaScript (ES6+), React.js, HTML5, CSS3, and Git.\nExperience building responsive single-page applications and consuming REST APIs.\nBasic familiarity with TypeScript.',
  fullstack:
    'Full-stack developer with experience in Python, FastAPI, JavaScript, React, and Node.js.\nProficient with SQL, PostgreSQL, SQLite, REST APIs, and Docker.\nStrong foundation in Git and Data Structures & Algorithms.',
  datascience:
    'Data Science student skilled in Python, SQL, Pandas, NumPy, and Scikit-learn.\nExperience with Exploratory Data Analysis (EDA), Data Visualization (Matplotlib), and Machine Learning.\nKnowledge of statistics and relational databases.'
};

export default function JobAnalyzer() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialJobId = searchParams.get('job_id');

  // Active Tab: 'analyze' or 'history'
  const [activeTab, setActiveTab] = useState('analyze');

  // Input Mode: 'saved' or 'manual'
  const [inputMode, setInputMode] = useState(initialJobId ? 'saved' : 'manual');

  // Saved Jobs for dropdown
  const [savedJobs, setSavedJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(initialJobId || '');
  const [selectedJobObj, setSelectedJobObj] = useState(null);

  // Form inputs
  const [companyName, setCompanyName] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [resumeText, setResumeText] = useState('');
  const [saveToHistory, setSaveToHistory] = useState(true);

  // State: loading, error, analysis result
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  // Session completed checklist IDs
  const [completedRecs, setCompletedRecs] = useState(new Set());

  // History state
  const [historyList, setHistoryList] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  // 1. Load saved applications for Option A dropdown
  const loadSavedJobs = useCallback(async () => {
    const res = await getApplications();
    if (res.ok && res.data) {
      setSavedJobs(res.data);
    }
  }, []);

  // 2. Load History
  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    const res = await getAnalysisHistory();
    if (res.ok && res.data) {
      setHistoryList(res.data);
    }
    setLoadingHistory(false);
  }, []);

  useEffect(() => {
    loadSavedJobs();
    loadHistory();
  }, [loadSavedJobs, loadHistory]);

  // 3. Handle initial job_id if query parameter exists
  useEffect(() => {
    if (initialJobId) {
      getApplicationById(initialJobId).then((res) => {
        if (res.ok && res.data) {
          setSelectedJobId(res.data.id.toString());
          setSelectedJobObj(res.data);
          setCompanyName(res.data.company_name || '');
          setJobTitle(res.data.job_title || '');
          setJobDescription(res.data.job_description || '');
          setInputMode('saved');
        }
      });
    }
  }, [initialJobId]);

  // When user selects a job from the dropdown in Option A
  const handleJobSelect = (e) => {
    const jId = e.target.value;
    setSelectedJobId(jId);
    if (!jId) {
      setSelectedJobObj(null);
      return;
    }
    const found = savedJobs.find((j) => j.id.toString() === jId);
    if (found) {
      setSelectedJobObj(found);
      setCompanyName(found.company_name || '');
      setJobTitle(found.job_title || '');
      setJobDescription(found.job_description || '');
      setError(null);
    }
  };

  // Run Analysis
  const handleRunAnalysis = async (e) => {
    e.preventDefault();
    setError(null);

    const trimmedJd = jobDescription.trim();
    if (!trimmedJd) {
      setError('Please provide a job description to analyze.');
      return;
    }
    if (trimmedJd.length < 20) {
      setError('Job description is too short (minimum 20 characters required for meaningful skill extraction).');
      return;
    }

    setAnalyzing(true);
    const payload = {
      job_description: trimmedJd,
      resume_or_profile_text: resumeText.trim() || null,
      job_id: inputMode === 'saved' && selectedJobId ? parseInt(selectedJobId, 10) : null,
      company_name: companyName.trim() || null,
      job_title: jobTitle.trim() || null,
      save_analysis: saveToHistory
    };

    const res = await analyzeJob(payload);
    setAnalyzing(false);

    if (res.ok && res.data) {
      setAnalysisResult(res.data);
      setCompletedRecs(new Set());
      if (saveToHistory) {
        loadHistory();
      }
    } else {
      setError(res.error || 'Analysis failed. Please check inputs and try again.');
    }
  };

  // Toggle recommendation completion
  const toggleRec = (recId) => {
    setCompletedRecs((prev) => {
      const next = new Set(prev);
      if (next.has(recId)) {
        next.delete(recId);
      } else {
        next.add(recId);
      }
      return next;
    });
  };

  // View historical analysis
  const handleViewHistorical = async (item) => {
    const res = await getAnalysisById(item.id);
    if (res.ok && res.data) {
      setAnalysisResult(res.data);
      setCompanyName(res.data.company_name || '');
      setJobTitle(res.data.job_title || '');
      setActiveTab('analyze');
      window.scrollTo({ top: 400, behavior: 'smooth' });
    }
  };

  // Delete history item
  const handleDeleteHistory = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this saved analysis record from history?')) return;
    setDeletingId(id);
    const res = await deleteAnalysis(id);
    setDeletingId(null);
    if (res.ok) {
      setHistoryList((prev) => prev.filter((item) => item.id !== id));
      if (analysisResult && analysisResult.id === id) {
        setAnalysisResult(null);
      }
    } else {
      alert(`Delete failed: ${res.error}`);
    }
  };

  return (
    <div className="analyzer-page fade-in">
      {/* 1. Page Header with Title & Tab Navigation */}
      <div className="analyzer-header">
        <div className="analyzer-title-group">
          <h1>
            <span>Job Description Analyzer</span>
          </h1>
          <p>
            Extract technical requirements, compare against your skill profile, and uncover actionable learning priorities.
          </p>
        </div>

        <div className="tab-nav">
          <button
            className={`tab-btn ${activeTab === 'analyze' ? 'active' : ''}`}
            onClick={() => setActiveTab('analyze')}
          >
            <FileSearch size={16} />
            <span>Analyze Job</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('history');
              loadHistory();
            }}
          >
            <History size={16} />
            <span>Past Analyses</span>
            <span className="tab-badge">{historyList.length}</span>
          </button>
        </div>
      </div>

      {activeTab === 'analyze' ? (
        <>
          {/* 2. Input Section */}
          <form onSubmit={handleRunAnalysis}>
            <div className="analyzer-input-grid">
              {/* Left Column: Job Description Input */}
              <div className="analyzer-input-card">
                <div className="input-card-header">
                  <h2>
                    <Briefcase size={18} color="var(--primary)" />
                    <span>Target Job Opportunity</span>
                  </h2>

                  {/* Option A vs Option B mode toggle */}
                  <div className="mode-toggle">
                    <button
                      type="button"
                      className={`mode-btn ${inputMode === 'saved' ? 'active' : ''}`}
                      onClick={() => setInputMode('saved')}
                    >
                      Option A: Saved Job
                    </button>
                    <button
                      type="button"
                      className={`mode-btn ${inputMode === 'manual' ? 'active' : ''}`}
                      onClick={() => setInputMode('manual')}
                    >
                      Option B: Paste New
                    </button>
                  </div>
                </div>

                {inputMode === 'saved' ? (
                  <div className="form-group">
                    <label className="form-label" htmlFor="saved-job-select">
                      Select from Application Tracker:
                    </label>
                    <select
                      id="saved-job-select"
                      className="form-select"
                      value={selectedJobId}
                      onChange={handleJobSelect}
                    >
                      <option value="">Choose a saved job...</option>
                      {savedJobs.map((j) => (
                        <option key={j.id} value={j.id}>
                          {j.company_name} — {j.job_title} ({j.application_status})
                        </option>
                      ))}
                    </select>

                    {selectedJobObj && (
                      <div className="selected-job-banner" style={{ marginTop: '0.5rem' }}>
                        <div>
                          <strong>{selectedJobObj.company_name}</strong> &bull; {selectedJobObj.job_title}
                          <div style={{ fontSize: '0.75rem', color: '#4338ca', marginTop: '0.2rem' }}>
                            Status: {selectedJobObj.application_status} &bull; Read-only integration
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label" htmlFor="manual-company">Company Name (Optional)</label>
                      <input
                        id="manual-company"
                        type="text"
                        className="form-input"
                        placeholder="e.g. Google, Amazon, Stripe"
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" htmlFor="manual-role">Job Role (Optional)</label>
                      <input
                        id="manual-role"
                        type="text"
                        className="form-input"
                        placeholder="e.g. Software Engineer Intern"
                        value={jobTitle}
                        onChange={(e) => setJobTitle(e.target.value)}
                      />
                    </div>
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label" htmlFor="jd-textarea">
                    Job Description Content <span className="required">*</span>
                  </label>
                  <textarea
                    id="jd-textarea"
                    rows="9"
                    className="form-textarea"
                    placeholder="Paste job posting text here including Required Qualifications, Responsibilities, and Preferred Skills..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span>Extracts React, Python, SQL, REST APIs, Git, DSA, Docker, etc.</span>
                    <span>{jobDescription.length} characters</span>
                  </div>
                </div>
              </div>

              {/* Right Column: User Skills / Resume Input */}
              <div className="analyzer-input-card">
                <div className="input-card-header">
                  <h2>
                    <Sparkles size={18} color="var(--secondary)" />
                    <span>Your Resume & Skill Profile</span>
                  </h2>

                  <div className="sample-fill-group">
                    <button
                      type="button"
                      className="sample-btn"
                      onClick={() => setResumeText(SAMPLE_PROFILES.frontend)}
                      title="Load Frontend Profile"
                    >
                      Frontend
                    </button>
                    <button
                      type="button"
                      className="sample-btn"
                      onClick={() => setResumeText(SAMPLE_PROFILES.fullstack)}
                      title="Load Full-Stack Profile"
                    >
                      Full-Stack
                    </button>
                    <button
                      type="button"
                      className="sample-btn"
                      onClick={() => setResumeText(SAMPLE_PROFILES.datascience)}
                      title="Load Data Science Profile"
                    >
                      Data Science
                    </button>
                    {resumeText && (
                      <button
                        type="button"
                        className="sample-btn"
                        onClick={() => setResumeText('')}
                        style={{ color: '#ef4444' }}
                      >
                        Clear
                      </button>
                    )}
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="resume-textarea">
                    Paste Resume Content or List Your Skills:
                  </label>
                  <textarea
                    id="resume-textarea"
                    rows="11"
                    className="form-textarea"
                    placeholder="Paste your resume sections, project tech stacks, or type: 'React, Python, SQL, REST APIs, Git'..."
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                  />
                  <span className="form-hint">
                    SkillBridge matches recognized technical competencies against employer expectations.
                  </span>
                </div>
              </div>
            </div>

            {/* Error Message if Validation Fails */}
            {error && (
              <div
                style={{
                  background: '#fee2e2',
                  border: '1px solid #fecaca',
                  color: '#991b1b',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginTop: '1rem'
                }}
              >
                <AlertTriangle size={18} />
                <span>{error}</span>
              </div>
            )}

            {/* Action Bar */}
            <div className="analyzer-action-strip" style={{ marginTop: '1.25rem' }}>
              <label className="save-checkbox-label">
                <input
                  type="checkbox"
                  checked={saveToHistory}
                  onChange={(e) => setSaveToHistory(e.target.checked)}
                />
                <span>Save this analysis to SQLite history for future review</span>
              </label>

              <button type="submit" className="btn-primary" disabled={analyzing}>
                <Sparkles size={18} />
                <span>{analyzing ? 'Extracting & Comparing Skills...' : 'Analyze Job Description'}</span>
              </button>
            </div>
          </form>

          {/* 3. Results Section */}
          {analysisResult && (
            <div className="results-container fade-in" style={{ marginTop: '2rem' }}>
              {/* A. Transparent Match Score Banner */}
              <div className="score-hero-card">
                <div className="score-details-left">
                  <div className="score-badge">
                    <Sparkles size={14} />
                    <span>Rule-Based Skill Coverage</span>
                  </div>
                  <h2>
                    {analysisResult.company_name
                      ? `${analysisResult.company_name} — ${analysisResult.job_title || 'Opportunity'}`
                      : 'Job Description Match Analysis'}
                  </h2>
                  <p>
                    {analysisResult.score_breakdown.message ||
                      'Transparent coverage calculation of recognized required and preferred qualifications.'}
                  </p>

                  <div className="score-formula-box">
                    <strong>Formula Breakdown: </strong>
                    <span>{analysisResult.score_breakdown.formula || 'Rule-based coverage'}</span>
                    <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.35rem', flexWrap: 'wrap' }}>
                      {analysisResult.score_breakdown.required_coverage && (
                        <span>
                          <strong>Required Skills: </strong>
                          {analysisResult.score_breakdown.required_coverage}
                        </span>
                      )}
                      {analysisResult.score_breakdown.preferred_coverage && (
                        <span>
                          <strong>Preferred Skills: </strong>
                          {analysisResult.score_breakdown.preferred_coverage}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Score Number Display */}
                <div className="score-circle-display">
                  <div className="score-number">
                    {analysisResult.match_score !== null ? `${analysisResult.match_score}%` : 'N/A'}
                  </div>
                  <div className="score-label">Skill Coverage</div>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="disclaimer-banner">
                <Info size={18} color="var(--primary)" style={{ flexShrink: 0 }} />
                <span>{analysisResult.disclaimer}</span>
              </div>

              {/* B. Four Skill Categorization Groups */}
              <div className="skills-comparison-grid">
                {/* 1. Matching Required Skills */}
                <div className="skill-category-card">
                  <div className="category-card-header">
                    <h3 style={{ color: '#065f46' }}>
                      <CheckCircle2 size={18} />
                      <span>Matching Required Skills ({analysisResult.matching_required.length})</span>
                    </h3>
                  </div>
                  {analysisResult.matching_required.length === 0 ? (
                    <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                      No matching required skills identified.
                    </p>
                  ) : (
                    <div className="skill-items-list">
                      {analysisResult.matching_required.map((item, idx) => (
                        <div key={idx} className="skill-pill-item matching-req">
                          <div>
                            <span className="skill-name-tag">{item.skill}</span>
                            <div className="skill-pill-explanation">{item.explanation}</div>
                          </div>
                          <span className="skill-domain-tag">{item.category}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 2. Missing Required Skills */}
                <div className="skill-category-card">
                  <div className="category-card-header">
                    <h3 style={{ color: '#991b1b' }}>
                      <XCircle size={18} />
                      <span>Missing Required Skills ({analysisResult.missing_required.length})</span>
                    </h3>
                  </div>
                  {analysisResult.missing_required.length === 0 ? (
                    <p style={{ fontSize: '0.825rem', color: '#059669', fontWeight: 600 }}>
                      🎉 Excellent! You have matched all explicitly required technical skills.
                    </p>
                  ) : (
                    <div className="skill-items-list">
                      {analysisResult.missing_required.map((item, idx) => (
                        <div key={idx} className="skill-pill-item missing-req">
                          <div>
                            <span className="skill-name-tag">{item.skill}</span>
                            <div className="skill-pill-explanation">{item.explanation}</div>
                          </div>
                          <span className="skill-domain-tag">{item.category}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 3. Matching Preferred Skills */}
                <div className="skill-category-card">
                  <div className="category-card-header">
                    <h3 style={{ color: '#0369a1' }}>
                      <CheckCircle2 size={18} />
                      <span>Matching Preferred Skills ({analysisResult.matching_preferred.length})</span>
                    </h3>
                  </div>
                  {analysisResult.matching_preferred.length === 0 ? (
                    <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                      No preferred bonus skills matched.
                    </p>
                  ) : (
                    <div className="skill-items-list">
                      {analysisResult.matching_preferred.map((item, idx) => (
                        <div key={idx} className="skill-pill-item matching-pref">
                          <div>
                            <span className="skill-name-tag">{item.skill}</span>
                            <div className="skill-pill-explanation">{item.explanation}</div>
                          </div>
                          <span className="skill-domain-tag">{item.category}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 4. Missing Preferred Skills */}
                <div className="skill-category-card">
                  <div className="category-card-header">
                    <h3 style={{ color: '#92400e' }}>
                      <AlertTriangle size={18} />
                      <span>Missing Preferred Skills ({analysisResult.missing_preferred.length})</span>
                    </h3>
                  </div>
                  {analysisResult.missing_preferred.length === 0 ? (
                    <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                      No missing preferred skills detected.
                    </p>
                  ) : (
                    <div className="skill-items-list">
                      {analysisResult.missing_preferred.map((item, idx) => (
                        <div key={idx} className="skill-pill-item missing-pref">
                          <div>
                            <span className="skill-name-tag">{item.skill}</span>
                            <div className="skill-pill-explanation">{item.explanation}</div>
                          </div>
                          <span className="skill-domain-tag">{item.category}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Unclassified Detected Skills (if any) */}
              {analysisResult.unclassified_skills.length > 0 && (
                <div className="skill-category-card">
                  <div className="category-card-header">
                    <h3>
                      <Layers size={18} />
                      <span>Additional Unclassified Skills Detected ({analysisResult.unclassified_skills.length})</span>
                    </h3>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    These skills appeared without explicit "Required" or "Preferred" section headings and were preserved transparently.
                  </p>
                  <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                    {analysisResult.unclassified_skills.map((s, idx) => (
                      <span key={idx} className="skill-tag">
                        {s.skill} ({s.matched_alias})
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Other Requirements (Education & Tooling) */}
              {analysisResult.other_requirements.length > 0 && (
                <div className="other-reqs-card">
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <GraduationCap size={18} color="var(--primary)" />
                    <span>Other Detected Requirements (Education & Infrastructure)</span>
                  </h3>
                  <div className="other-reqs-grid">
                    {analysisResult.other_requirements.map((req, idx) => (
                      <div key={idx} className="other-req-item">
                        <strong style={{ color: 'var(--text-main)' }}>{req.type}:</strong>
                        <span>{req.detail}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* C. Prioritized Learning Checklist */}
              {analysisResult.recommendations.length > 0 && (
                <div className="recommendations-card">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)' }}>
                        Prioritized Learning Checklist & Skill Gaps
                      </h3>
                      <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                        Concrete next steps and project tasks to close detected qualification gaps.
                      </p>
                    </div>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--primary)' }}>
                      {completedRecs.size} of {analysisResult.recommendations.length} completed
                    </span>
                  </div>

                  <div className="recommendations-list">
                    {analysisResult.recommendations.map((rec) => {
                      const isDone = completedRecs.has(rec.id);
                      return (
                        <div
                          key={rec.id}
                          className={`rec-item-card ${isDone ? 'completed' : ''}`}
                        >
                          <input
                            type="checkbox"
                            className="rec-checkbox"
                            checked={isDone}
                            onChange={() => toggleRec(rec.id)}
                            aria-label={`Mark ${rec.skill} recommendation as completed`}
                          />
                          <div className="rec-content">
                            <div className="rec-title-row">
                              <span className="rec-skill-name" style={{ textDecoration: isDone ? 'line-through' : 'none' }}>
                                {rec.skill}
                              </span>
                              <span className={`priority-badge priority-${rec.priority.toLowerCase()}`}>
                                {rec.priority} Priority
                              </span>
                              <span className="rec-reason">{rec.reason}</span>
                            </div>
                            <p className="rec-action">{rec.suggested_action}</p>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.4rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                              <div className="rec-topics-tag" style={{ margin: 0 }}>
                                <BookOpen size={13} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                                <span>Key Topics: {rec.learning_topic}</span>
                              </div>
                              <button
                                type="button"
                                className="btn-secondary"
                                style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem', height: 'auto' }}
                                onClick={() => navigate(`/questions?search=${encodeURIComponent(rec.skill)}`)}
                                title={`Search interview questions about ${rec.skill}`}
                              >
                                <HelpCircle size={12} />
                                <span>View Questions for {rec.skill}</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Cross-Module Action Bar */}
                  <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-card)', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      Ready to test your readiness for <strong>{companyName || 'this role'}</strong>?
                    </span>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => navigate(`/questions?company_name=${encodeURIComponent(companyName || '')}`)}
                      >
                        <HelpCircle size={14} />
                        <span>Logged Questions ({companyName || 'Company'})</span>
                      </button>
                      <button
                        type="button"
                        className="btn-primary"
                        onClick={() => navigate(`/practice?job_id=${selectedJobId || ''}&target_company=${encodeURIComponent(companyName || '')}`)}
                      >
                        <Mic size={14} />
                        <span>Practice Mock Interview</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        /* 4. History Tab */
        <div className="fade-in">
          <div style={{ marginBottom: '1.25rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Analysis History
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Review past job descriptions and skill coverage scores stored in your database.
            </p>
          </div>

          {loadingHistory ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              Loading past analyses...
            </div>
          ) : historyList.length === 0 ? (
            <div className="empty-state-box">
              <div className="empty-icon-circle">
                <History size={28} />
              </div>
              <h3>No analysis history yet</h3>
              <p>
                Analyze a job description and check "Save this analysis" to review your match results later.
              </p>
              <button className="btn-primary" onClick={() => setActiveTab('analyze')}>
                Analyze a Job
              </button>
            </div>
          ) : (
            <div className="history-grid">
              {historyList.map((item) => (
                <div
                  key={item.id}
                  className="history-card"
                  onClick={() => handleViewHistorical(item)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="history-card-header">
                    <div>
                      <div className="history-company">
                        {item.company_name || 'Independent Analysis'}
                      </div>
                      <div className="history-role">
                        {item.job_title || 'General Job Posting'}
                      </div>
                    </div>
                    <div className="history-score-chip">
                      {item.match_score !== null ? `${item.match_score}%` : 'N/A'}
                    </div>
                  </div>

                  <div className="history-meta-row">
                    <span>
                      <strong style={{ color: '#059669' }}>{item.matching_count}</strong> matched
                    </span>
                    <span>&bull;</span>
                    <span>
                      <strong style={{ color: '#dc2626' }}>{item.missing_count}</strong> missing
                    </span>
                    <span>&bull;</span>
                    <span>{item.required_count} required</span>
                  </div>

                  <div className="history-actions">
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-light)' }}>
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent'}
                    </span>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button
                        className="card-link-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewHistorical(item);
                        }}
                      >
                        <span>View Details</span>
                        <ArrowRight size={13} />
                      </button>
                      <button
                        className="action-icon-btn delete"
                        onClick={(e) => handleDeleteHistory(item.id, e)}
                        title="Delete from history"
                        disabled={deletingId === item.id}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
