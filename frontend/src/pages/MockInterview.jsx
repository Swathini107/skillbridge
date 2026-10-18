import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Mic,
  Play,
  CheckCircle,
  Clock,
  Briefcase,
  AlertCircle,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Save,
  SkipForward,
  Star,
  Award,
  Sparkles,
  RefreshCw,
  Trash2,
  FileText,
  Eye,
  Pause,
  AlertTriangle,
  Lightbulb
} from 'lucide-react';
import {
  previewPracticeSession,
  startPracticeSession,
  getPracticeSessions,
  getPracticeSessionById,
  updatePracticeAnswer,
  finishPracticeSession,
  resumePracticeSession,
  getPracticeSessionReport,
  deletePracticeSession,
  getApplications
} from '../services/api';
import '../styles/practice.css';

const ROUND_TYPES = [
  'Technical',
  'HR',
  'Aptitude',
  'Behavioral',
  'System Design'
];

const DIFFICULTIES = ['Beginner', 'Intermediate', 'Advanced', 'Mixed'];
const QUESTION_COUNTS = [5, 10, 15];
const TIME_LIMITS = [
  { label: 'No time limit', value: null },
  { label: '5 minutes', value: 5 },
  { label: '10 minutes', value: 10 },
  { label: '15 minutes', value: 15 },
  { label: '20 minutes', value: 20 }
];

export default function MockInterview() {
  const [searchParams] = useSearchParams();
  const paramJobId = searchParams.get('job_id');
  const paramRound = searchParams.get('round_type');
  const paramResumeId = searchParams.get('resume_id');
  const paramViewReport = searchParams.get('view_report');

  // Navigation tabs: 'setup' | 'runner' | 'report' | 'history'
  const [activeTab, setActiveTab] = useState('setup');

  // Available saved jobs for targeting
  const [savedJobs, setSavedJobs] = useState([]);

  // Setup Form State
  const [setupForm, setSetupForm] = useState({
    session_name: 'Frontend Internship Practice — Round 1',
    round_type: 'Technical',
    job_id: '',
    target_role: '',
    target_company: '',
    question_source: 'Memory Bank',
    selected_topic: '',
    difficulty: 'Mixed',
    question_count: 5,
    time_limit_minutes: 15,
    include_custom: false,
    custom_question_text: '',
    custom_expected_answer: ''
  });

  // Preview state
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [setupError, setSetupError] = useState(null);
  const [isStarting, setIsStarting] = useState(false);

  // Live Practice Runner State
  const [activeSession, setActiveSession] = useState(null);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answerText, setAnswerText] = useState('');
  const [selfRatings, setSelfRatings] = useState({});
  const [reflection, setReflection] = useState({
    went_well: '',
    was_difficult: '',
    need_to_learn: '',
    better_approach: ''
  });
  const [isGuidanceOpen, setIsGuidanceOpen] = useState(true);
  const [isSelfReviewOpen, setIsSelfReviewOpen] = useState(false);
  const [autosaveStatus, setAutosaveStatus] = useState('saved'); // 'saved' | 'saving' | 'error'
  const [timeRemainingSeconds, setTimeRemainingSeconds] = useState(null);
  const [elapsedDurationSeconds, setElapsedDurationSeconds] = useState(0);
  const [isTimerPaused, setIsTimerPaused] = useState(false);
  const [showFinishConfirm, setShowFinishConfirm] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);

  // Completed Session Report State
  const [reportData, setReportData] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);

  // History State
  const [historyList, setHistoryList] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const [historyStatusFilter, setHistoryStatusFilter] = useState('All');
  const [historyRoundFilter, setHistoryRoundFilter] = useState('All');

  // Autosave timer ref
  const autosaveTimeoutRef = useRef(null);

  // Load Session into Live Runner
  const loadSessionIntoRunner = useCallback((session) => {
    setActiveSession(session);
    const initialIndex = Math.min(
      session.current_question_index || 0,
      Math.max(0, (session.answers?.length || 1) - 1)
    );
    setCurrentQIndex(initialIndex);

    const currentAnswer = session.answers?.[initialIndex];
    if (currentAnswer) {
      setAnswerText(currentAnswer.answer_text || '');
      setSelfRatings(currentAnswer.self_ratings || {});
      setReflection({
        went_well: currentAnswer.went_well || '',
        was_difficult: currentAnswer.was_difficult || '',
        need_to_learn: currentAnswer.need_to_learn || '',
        better_approach: currentAnswer.better_approach || ''
      });
    }

    setElapsedDurationSeconds(session.duration_seconds || 0);

    // Initialize timer
    if (session.time_limit_minutes) {
      const totalAllowedSecs = session.time_limit_minutes * 60;
      const remaining = Math.max(0, totalAllowedSecs - (session.duration_seconds || 0));
      setTimeRemainingSeconds(remaining);
    } else {
      setTimeRemainingSeconds(null);
    }

    setIsTimerPaused(false);
    setActiveTab('runner');
  }, []);

  // 1. Fetch saved jobs on component mount
  const fetchSavedJobs = useCallback(async () => {
    const res = await getApplications({ status: 'All' });
    if (res.ok && res.data) {
      setSavedJobs(res.data);
    }
  }, []);

  // 2. Fetch history sessions
  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    const params = {};
    if (historyStatusFilter !== 'All') params.status = historyStatusFilter;
    if (historyRoundFilter !== 'All') params.round_type = historyRoundFilter;
    if (historySearch.trim()) params.search = historySearch.trim();

    const res = await getPracticeSessions(params);
    if (res.ok && res.data) {
      setHistoryList(res.data);
    }
    setHistoryLoading(false);
  }, [historyStatusFilter, historyRoundFilter, historySearch]);

  useEffect(() => {
    fetchSavedJobs();
  }, [fetchSavedJobs]);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab, fetchHistory]);

  // Check for existing active session stored in localStorage on initial load
  useEffect(() => {
    if (paramResumeId) {
      resumePracticeSession(parseInt(paramResumeId, 10)).then((res) => {
        if (res.ok && res.data) {
          localStorage.setItem('skillbridge_practice_session_id', res.data.id.toString());
          loadSessionIntoRunner(res.data);
        }
      });
    } else if (paramViewReport) {
      setReportLoading(true);
      getPracticeSessionReport(parseInt(paramViewReport, 10)).then((res) => {
        if (res.ok && res.data) {
          setReportData(res.data);
          setActiveTab('report');
        }
        setReportLoading(false);
      });
    } else {
      const savedSessionId = localStorage.getItem('skillbridge_practice_session_id');
      if (savedSessionId) {
        getPracticeSessionById(savedSessionId).then((res) => {
          if (res.ok && res.data) {
            if (res.data.status === 'In Progress') {
              loadSessionIntoRunner(res.data);
            }
          }
        });
      }
    }
  }, [paramResumeId, paramViewReport, loadSessionIntoRunner]);

  // Pre-populate setup form when navigated with job_id or round_type
  useEffect(() => {
    if (paramJobId && savedJobs.length > 0) {
      const found = savedJobs.find((j) => j.id.toString() === paramJobId.toString());
      if (found) {
        setSetupForm((prev) => ({
          ...prev,
          job_id: found.id,
          target_company: found.company_name,
          target_role: found.job_title,
          round_type: paramRound || prev.round_type,
          session_name: `${found.company_name} — ${paramRound || prev.round_type} Practice`
        }));
      }
    } else if (paramRound) {
      setSetupForm((prev) => ({
        ...prev,
        round_type: paramRound,
        session_name: `Targeted ${paramRound} Practice`
      }));
    }
  }, [paramJobId, paramRound, savedJobs]);

  // 3. Trigger live preview whenever setup form key fields change
  const triggerPreview = useCallback(async (formValues) => {
    setPreviewLoading(true);
    setSetupError(null);

    const payload = {
      session_name: formValues.session_name || 'Mock Interview Practice',
      round_type: formValues.round_type,
      job_id: formValues.job_id ? parseInt(formValues.job_id, 10) : null,
      target_company: formValues.target_company || null,
      target_role: formValues.target_role || null,
      question_source: formValues.question_source,
      selected_topic: formValues.selected_topic || null,
      difficulty: formValues.difficulty,
      question_count: formValues.question_count,
      time_limit_minutes: formValues.time_limit_minutes,
      custom_question:
        formValues.include_custom && formValues.custom_question_text.trim()
          ? {
              question_text: formValues.custom_question_text.trim(),
              round_type: formValues.round_type,
              expected_answer: formValues.custom_expected_answer.trim() || null
            }
          : null
    };

    const res = await previewPracticeSession(payload);
    if (res.ok && res.data) {
      setPreviewData(res.data);
    } else {
      setSetupError(res.error || 'Failed to load preview');
    }
    setPreviewLoading(false);
  }, []);

  // Update preview whenever round, job, difficulty, or count changes in setup
  useEffect(() => {
    if (activeTab === 'setup') {
      const handler = setTimeout(() => {
        triggerPreview(setupForm);
      }, 300);
      return () => clearTimeout(handler);
    }
  }, [
    activeTab,
    setupForm.round_type,
    setupForm.job_id,
    setupForm.difficulty,
    setupForm.question_count,
    setupForm.question_source,
    setupForm.selected_topic,
    setupForm.include_custom,
    setupForm.custom_question_text,
    triggerPreview
  ]);

  // Handle saved job selection change
  const handleJobSelect = (jobIdStr) => {
    if (!jobIdStr) {
      setSetupForm((prev) => ({
        ...prev,
        job_id: '',
        target_company: '',
        target_role: ''
      }));
      return;
    }
    const foundJob = savedJobs.find((j) => j.id.toString() === jobIdStr);
    if (foundJob) {
      setSetupForm((prev) => ({
        ...prev,
        job_id: foundJob.id,
        target_company: foundJob.company_name,
        target_role: foundJob.job_title,
        session_name: `${foundJob.company_name} — ${prev.round_type} Practice`
      }));
    }
  };

  // 4. Start Practice Session
  const handleStartSession = async () => {
    setIsStarting(true);
    setSetupError(null);

    const payload = {
      session_name: setupForm.session_name.trim() || 'Mock Interview Practice',
      round_type: setupForm.round_type,
      job_id: setupForm.job_id ? parseInt(setupForm.job_id, 10) : null,
      target_company: setupForm.target_company || null,
      target_role: setupForm.target_role || null,
      question_source: setupForm.question_source,
      selected_topic: setupForm.selected_topic || null,
      difficulty: setupForm.difficulty,
      question_count: setupForm.question_count,
      time_limit_minutes: setupForm.time_limit_minutes,
      custom_question:
        setupForm.include_custom && setupForm.custom_question_text.trim()
          ? {
              question_text: setupForm.custom_question_text.trim(),
              round_type: setupForm.round_type,
              expected_answer: setupForm.custom_expected_answer.trim() || null
            }
          : null
    };

    const res = await startPracticeSession(payload);
    if (res.ok && res.data) {
      localStorage.setItem('skillbridge_practice_session_id', res.data.id);
      loadSessionIntoRunner(res.data);
    } else {
      setSetupError(res.error || 'Failed to start practice session.');
    }
    setIsStarting(false);
  };

  // 6. Countdown / Elapsed Timer Effect
  useEffect(() => {
    if (activeTab !== 'runner' || isTimerPaused || !activeSession) return;

    const timerInterval = setInterval(() => {
      setElapsedDurationSeconds((prev) => prev + 1);

      if (timeRemainingSeconds !== null) {
        setTimeRemainingSeconds((prev) => {
          if (prev <= 1) {
            return 0;
          }
          return prev - 1;
        });
      }
    }, 1000);

    return () => clearInterval(timerInterval);
  }, [activeTab, isTimerPaused, activeSession, timeRemainingSeconds]);

  // Format seconds to MM:SS
  const formatTime = (secs) => {
    if (secs === null || secs === undefined) return '00:00';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // 7. Autosave / Save current question answer
  const saveCurrentAnswer = useCallback(
    async (overrideAnswer, overrideRatings, overrideReflection, overrideSkipped) => {
      if (!activeSession || !activeSession.answers || !activeSession.answers[currentQIndex]) return;

      const currentAnswerRecord = activeSession.answers[currentQIndex];
      setAutosaveStatus('saving');

      const textToSave = overrideAnswer !== undefined ? overrideAnswer : answerText;
      const ratingsToSave = overrideRatings !== undefined ? overrideRatings : selfRatings;
      const refToSave = overrideReflection !== undefined ? overrideReflection : reflection;
      const skippedToSave = overrideSkipped !== undefined ? overrideSkipped : currentAnswerRecord.is_skipped;

      const payload = {
        answer_text: textToSave,
        is_attempted: textToSave.trim().length > 0 && !skippedToSave,
        is_skipped: skippedToSave,
        self_ratings: ratingsToSave,
        went_well: refToSave.went_well || null,
        was_difficult: refToSave.was_difficult || null,
        need_to_learn: refToSave.need_to_learn || null,
        better_approach: refToSave.better_approach || null
      };

      const res = await updatePracticeAnswer(activeSession.id, currentAnswerRecord.id, payload, {
        current_index: currentQIndex,
        duration_seconds: elapsedDurationSeconds
      });

      if (res.ok && res.data) {
        setAutosaveStatus('saved');
        // Update local activeSession answers array
        setActiveSession((prev) => {
          if (!prev) return prev;
          const updatedAnswers = [...prev.answers];
          updatedAnswers[currentQIndex] = res.data;
          return {
            ...prev,
            answers: updatedAnswers,
            current_question_index: currentQIndex,
            duration_seconds: elapsedDurationSeconds
          };
        });
      } else {
        setAutosaveStatus('error');
      }
    },
    [activeSession, currentQIndex, answerText, selfRatings, reflection, elapsedDurationSeconds]
  );

  // Debounced autosave on typing in textarea
  const handleAnswerChange = (e) => {
    const val = e.target.value;
    setAnswerText(val);
    setAutosaveStatus('saving');

    if (autosaveTimeoutRef.current) {
      clearTimeout(autosaveTimeoutRef.current);
    }
    autosaveTimeoutRef.current = setTimeout(() => {
      saveCurrentAnswer(val, undefined, undefined, false);
    }, 1200);
  };

  // 8. Navigation between questions
  const switchQuestion = async (targetIndex) => {
    if (targetIndex < 0 || !activeSession?.answers || targetIndex >= activeSession.answers.length) {
      return;
    }

    // Save current question before switching
    await saveCurrentAnswer();

    // Load next question into state
    setCurrentQIndex(targetIndex);
    const nextAns = activeSession.answers[targetIndex];
    if (nextAns) {
      setAnswerText(nextAns.answer_text || '');
      setSelfRatings(nextAns.self_ratings || {});
      setReflection({
        went_well: nextAns.went_well || '',
        was_difficult: nextAns.was_difficult || '',
        need_to_learn: nextAns.need_to_learn || '',
        better_approach: nextAns.better_approach || ''
      });
    }
  };

  // 9. Skip current question
  const handleSkipQuestion = async () => {
    await saveCurrentAnswer(undefined, undefined, undefined, true);
    if (currentQIndex < (activeSession?.answers?.length || 0) - 1) {
      switchQuestion(currentQIndex + 1);
    }
  };

  // 10. Self-Review Rating helper
  const handleRatingChange = (criterionKey, score) => {
    const updated = {
      ...selfRatings,
      [criterionKey]: score
    };
    setSelfRatings(updated);
    saveCurrentAnswer(undefined, updated, undefined, undefined);
  };

  const handleReflectionChange = (field, value) => {
    const updated = {
      ...reflection,
      [field]: value
    };
    setReflection(updated);
    saveCurrentAnswer(undefined, undefined, updated, undefined);
  };

  // 11. Finish Practice Session
  const handleFinishSession = async () => {
    setIsFinishing(true);
    // Final save on current question
    await saveCurrentAnswer();

    const res = await finishPracticeSession(activeSession.id, {
      duration_seconds: elapsedDurationSeconds
    });

    if (res.ok && res.data) {
      localStorage.removeItem('skillbridge_practice_session_id');
      setReportData(res.data);
      setActiveSession(null);
      setShowFinishConfirm(false);
      setActiveTab('report');
    }
    setIsFinishing(false);
  };

  // 12. Review completed session from history
  const handleReviewHistorySession = async (sessionId) => {
    setReportLoading(true);
    const res = await getPracticeSessionReport(sessionId);
    if (res.ok && res.data) {
      setReportData(res.data);
      setActiveTab('report');
    }
    setReportLoading(false);
  };

  // 13. Resume in-progress session from history
  const handleResumeHistorySession = async (sessionId) => {
    const res = await resumePracticeSession(sessionId);
    if (res.ok && res.data) {
      localStorage.setItem('skillbridge_practice_session_id', res.data.id);
      loadSessionIntoRunner(res.data);
    }
  };

  // 14. Delete session from history
  const handleDeleteSession = async (sessionId) => {
    if (window.confirm('Are you sure you want to delete this practice session? Original questions and jobs will remain safe.')) {
      await deletePracticeSession(sessionId);
      fetchHistory();
    }
  };

  // Determine applicable criteria for current question
  const currentQ = activeSession?.answers?.[currentQIndex];
  const roundTypeForReview = currentQ?.round_type || activeSession?.round_type || 'Technical';
  const isHRRound = ['HR', 'Behavioral'].includes(roundTypeForReview);

  const criteriaToRender = [
    { key: 'clarity', label: 'Clarity of Communication' },
    { key: 'completeness', label: 'Completeness & Depth' },
    { key: 'confidence', label: 'Delivery Confidence' },
    ...(isHRRound
      ? [
          { key: 'answer_structure', label: 'Answer Structure (STAR Method)' },
          { key: 'specific_examples', label: 'Concrete & Specific Examples' }
        ]
      : [
          { key: 'technical_correctness', label: 'Technical Accuracy & Edge Cases' },
          { key: 'problem_solving', label: 'Problem-Solving Methodology' }
        ])
  ];

  return (
    <div className="practice-container">
      {/* Top Header & Workflow Tabs */}
      <div className="practice-header">
        <div className="practice-header-top">
          <div className="practice-title-group">
            <h1>Mock Interview Practice Studio</h1>
            <p>
              Interactive role-specific interview simulation with targeted skill-gap preparation and structured self-review.
            </p>
          </div>
          {activeSession && activeTab !== 'runner' && (
            <button
              className="runner-btn runner-btn-primary"
              onClick={() => setActiveTab('runner')}
            >
              <Mic size={16} /> Return to Active Interview
            </button>
          )}
        </div>

        <div className="practice-tabs">
          <button
            className={`practice-tab-btn ${activeTab === 'setup' ? 'active' : ''}`}
            onClick={() => setActiveTab('setup')}
          >
            <Sparkles size={16} /> 1. Setup Session
          </button>
          {activeSession && (
            <button
              className={`practice-tab-btn ${activeTab === 'runner' ? 'active' : ''}`}
              onClick={() => setActiveTab('runner')}
            >
              <Mic size={16} /> 2. Live Interview
            </button>
          )}
          {reportData && (
            <button
              className={`practice-tab-btn ${activeTab === 'report' ? 'active' : ''}`}
              onClick={() => setActiveTab('report')}
            >
              <Award size={16} /> 3. Performance Summary
            </button>
          )}
          <button
            className={`practice-tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <Clock size={16} /> Practice History
          </button>
        </div>
      </div>

      {/* =================================================================== */}
      {/* STAGE 1: PRACTICE SESSION SETUP                                     */}
      {/* =================================================================== */}
      {activeTab === 'setup' && (
        <div className="setup-layout-grid">
          {/* Left Column: Configuration Form */}
          <div className="setup-form-card">
            <h2 className="setup-section-title">
              <Sparkles size={20} color="#2563eb" /> Configure Your Practice Session
            </h2>

            {setupError && (
              <div className="alert-box" style={{ background: '#fef2f2', border: '1px solid #fecaca', padding: '0.75rem 1rem', borderRadius: '8px', color: '#b91c1c', marginBottom: '1rem', fontSize: '0.9rem' }}>
                <AlertCircle size={16} style={{ display: 'inline', marginRight: '6px' }} />
                {setupError}
              </div>
            )}

            {/* Session Name */}
            <div className="setup-form-group">
              <label htmlFor="session-name-input">Session Name</label>
              <input
                id="session-name-input"
                type="text"
                value={setupForm.session_name}
                onChange={(e) => setSetupForm({ ...setupForm, session_name: e.target.value })}
                placeholder="e.g., Google Frontend Mock Round 1"
              />
            </div>

            {/* Interview Round */}
            <div className="setup-form-group">
              <label>Interview Round</label>
              <div className="pill-grid">
                {ROUND_TYPES.map((round) => (
                  <button
                    key={round}
                    type="button"
                    className={`pill-option-btn ${setupForm.round_type === round ? 'active' : ''}`}
                    onClick={() => setSetupForm({ ...setupForm, round_type: round })}
                  >
                    {round}
                  </button>
                ))}
              </div>
            </div>

            {/* Target Role & Saved Job Selection (Personalization!) */}
            <div className="setup-form-group">
              <label htmlFor="saved-job-select">Target Opportunity (Optional Personalization)</label>
              <select
                id="saved-job-select"
                value={setupForm.job_id}
                onChange={(e) => handleJobSelect(e.target.value)}
              >
                <option value="">-- No specific job (Use general Question Bank) --</option>
                {savedJobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.company_name} — {job.job_title} ({job.application_status})
                  </option>
                ))}
              </select>
              <span className="field-hint">
                Selecting a saved job prioritizes associated questions and targets skill gaps identified by the Job Analyzer.
              </span>

              {setupForm.job_id && previewData?.personalized_skills_targeted?.length > 0 && (
                <div className="personalized-job-banner">
                  <div className="personalized-badge">
                    <Sparkles size={14} /> Personalized Skills Targeted:
                  </div>
                  <div className="targeted-skills-tag-list">
                    {previewData.personalized_skills_targeted.map((skill) => (
                      <span key={skill} className="targeted-skill-chip">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Manual Target Role if not selected from job */}
            {!setupForm.job_id && (
              <div className="setup-form-group">
                <label htmlFor="target-role-input">Target Job Role</label>
                <input
                  id="target-role-input"
                  type="text"
                  value={setupForm.target_role}
                  onChange={(e) => setSetupForm({ ...setupForm, target_role: e.target.value })}
                  placeholder="e.g. Full Stack Developer, Data Analyst"
                />
              </div>
            )}

            {/* Question Source */}
            <div className="setup-form-group">
              <label>Question Source</label>
              <div className="pill-grid">
                {['Memory Bank', 'Company/Job', 'Topic', 'Custom'].map((source) => (
                  <button
                    key={source}
                    type="button"
                    className={`pill-option-btn ${setupForm.question_source === source ? 'active' : ''}`}
                    onClick={() => setSetupForm({ ...setupForm, question_source: source })}
                  >
                    {source}
                  </button>
                ))}
              </div>
            </div>

            {/* Specific Topic if question source is Topic */}
            {setupForm.question_source === 'Topic' && (
              <div className="setup-form-group">
                <label htmlFor="topic-input">Filter by Topic</label>
                <input
                  id="topic-input"
                  type="text"
                  value={setupForm.selected_topic}
                  onChange={(e) => setSetupForm({ ...setupForm, selected_topic: e.target.value })}
                  placeholder="e.g. React, SQL, Algorithms, Leadership"
                />
              </div>
            )}

            {/* Question Count & Difficulty */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="setup-form-group">
                <label>Question Count</label>
                <div className="pill-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                  {QUESTION_COUNTS.map((count) => (
                    <button
                      key={count}
                      type="button"
                      className={`pill-option-btn ${setupForm.question_count === count ? 'active' : ''}`}
                      onClick={() => setSetupForm({ ...setupForm, question_count: count })}
                    >
                      {count} Qs
                    </button>
                  ))}
                </div>
              </div>

              <div className="setup-form-group">
                <label>Difficulty</label>
                <select
                  value={setupForm.difficulty}
                  onChange={(e) => setSetupForm({ ...setupForm, difficulty: e.target.value })}
                >
                  {DIFFICULTIES.map((diff) => (
                    <option key={diff} value={diff}>
                      {diff}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Optional Time Limit */}
            <div className="setup-form-group">
              <label>Time Limit</label>
              <select
                value={setupForm.time_limit_minutes ?? ''}
                onChange={(e) =>
                  setSetupForm({
                    ...setupForm,
                    time_limit_minutes: e.target.value ? parseInt(e.target.value, 10) : null
                  })
                }
              >
                {TIME_LIMITS.map((t) => (
                  <option key={t.label} value={t.value ?? ''}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Custom Question Toggle */}
            <div className="setup-form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={setupForm.include_custom}
                  onChange={(e) => setSetupForm({ ...setupForm, include_custom: e.target.checked })}
                />
                Include a custom question in this session
              </label>

              {setupForm.include_custom && (
                <div className="custom-question-box">
                  <label htmlFor="custom-q-text">Custom Question Text</label>
                  <input
                    id="custom-q-text"
                    type="text"
                    value={setupForm.custom_question_text}
                    onChange={(e) => setSetupForm({ ...setupForm, custom_question_text: e.target.value })}
                    placeholder="Type a specific question you want to practice..."
                  />
                  <label htmlFor="custom-q-expected">Key Talking Points or Expected Answer (Optional)</label>
                  <textarea
                    id="custom-q-expected"
                    rows={2}
                    value={setupForm.custom_expected_answer}
                    onChange={(e) => setSetupForm({ ...setupForm, custom_expected_answer: e.target.value })}
                    placeholder="Hints, algorithm steps, or key principles to review later..."
                  />
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Live Session Preview */}
          <div className="preview-summary-card">
            <h2 className="setup-section-title">
              <Eye size={20} color="#2563eb" /> Practice Session Preview
            </h2>

            {previewLoading ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                <RefreshCw size={24} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
                <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>Analyzing matching questions...</p>
              </div>
            ) : previewData ? (
              <>
                <div className="preview-stat-row">
                  <span className="preview-stat-label">Round Type</span>
                  <span className="preview-stat-value">{setupForm.round_type}</span>
                </div>
                <div className="preview-stat-row">
                  <span className="preview-stat-label">Target Role</span>
                  <span className="preview-stat-value">
                    {previewData.target_company
                      ? `${previewData.target_company} — ${previewData.target_role || setupForm.target_role || 'General'}`
                      : setupForm.target_role || 'General Role'}
                  </span>
                </div>
                <div className="preview-stat-row">
                  <span className="preview-stat-label">Questions Selected</span>
                  <span className="preview-stat-value">
                    {previewData.selected_count} / {previewData.requested_count} requested
                  </span>
                </div>
                <div className="preview-stat-row">
                  <span className="preview-stat-label">Time Limit</span>
                  <span className="preview-stat-value">
                    {setupForm.time_limit_minutes ? `${setupForm.time_limit_minutes} minutes` : 'No time limit'}
                  </span>
                </div>

                {previewData.warning && (
                  <div style={{ background: '#fffbeb', border: '1px solid #fef3c7', borderRadius: '8px', padding: '0.75rem', fontSize: '0.82rem', color: '#92400e' }}>
                    <AlertTriangle size={14} style={{ display: 'inline', marginRight: '5px' }} />
                    {previewData.warning}
                  </div>
                )}

                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginTop: '0.5rem' }}>
                  Selected Questions ({previewData.questions.length})
                </div>

                <div className="preview-questions-list">
                  {previewData.questions.map((q, idx) => (
                    <div key={idx} className="preview-q-item">
                      <div className="preview-q-text">
                        {idx + 1}. {q.question_text}
                      </div>
                      <div className="preview-q-meta">
                        <span>{q.difficulty}</span>
                        {q.topic && <span>• {q.topic}</span>}
                        {q.relevance_reason && (
                          <span className="preview-q-reason">• {q.relevance_reason}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="setup-action-group">
                  <button
                    className="start-session-btn"
                    disabled={isStarting || previewData.questions.length === 0}
                    onClick={handleStartSession}
                  >
                    {isStarting ? (
                      <>Starting Practice Session...</>
                    ) : (
                      <>
                        <Play size={18} /> Start Mock Interview ({previewData.questions.length} Questions)
                      </>
                    )}
                  </button>
                  <p style={{ textAlign: 'center', fontSize: '0.78rem', color: '#64748b' }}>
                    Your responses will be autosaved. You can review your progress or resume anytime.
                  </p>
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                <HelpCircle size={32} style={{ opacity: 0.5, marginBottom: '0.5rem' }} />
                <p>Configure your session to see a live preview of questions.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* STAGE 2: LIVE INTERVIEW PRACTICE RUNNER                             */}
      {/* =================================================================== */}
      {activeTab === 'runner' && activeSession && (
        <div className="practice-runner-container">
          {/* Runner Header Bar */}
          <div className="runner-header-bar">
            <div className="runner-session-title">
              <h2>{activeSession.session_name}</h2>
              <span className="runner-round-badge">{activeSession.round_type}</span>
              <span className="meta-chip">{activeSession.difficulty}</span>
              {activeSession.target_company && (
                <span className="meta-chip" style={{ background: '#f5f3ff', color: '#6d28d9' }}>
                  <Briefcase size={12} style={{ display: 'inline', marginRight: '4px' }} />
                  {activeSession.target_company}
                </span>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              {/* Timer Widget */}
              {activeSession.time_limit_minutes ? (
                <div
                  className={`runner-timer-widget ${
                    timeRemainingSeconds !== null && timeRemainingSeconds <= 120 ? 'warning' : ''
                  }`}
                >
                  <Clock size={16} />
                  <span className="timer-time-display">{formatTime(timeRemainingSeconds)}</span>
                  <button
                    className="timer-pause-btn"
                    onClick={() => setIsTimerPaused(!isTimerPaused)}
                    title={isTimerPaused ? 'Resume Timer' : 'Pause Timer'}
                  >
                    {isTimerPaused ? <Play size={14} /> : <Pause size={14} />}
                  </button>
                </div>
              ) : (
                <div className="runner-timer-widget">
                  <Clock size={16} />
                  <span className="timer-time-display">{formatTime(elapsedDurationSeconds)}</span>
                </div>
              )}

              <button
                className="runner-btn runner-btn-finish"
                onClick={() => setShowFinishConfirm(true)}
              >
                <CheckCircle size={16} /> Finish Interview
              </button>
            </div>
          </div>

          {/* Question Navigation Strip */}
          <div className="question-nav-strip">
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', marginRight: '0.5rem', whiteSpace: 'nowrap' }}>
              Questions:
            </span>
            {activeSession.answers?.map((ans, idx) => {
              const isCurrent = idx === currentQIndex;
              const isAtt = ans.is_attempted;
              const isSkp = ans.is_skipped;
              return (
                <button
                  key={ans.id || idx}
                  className={`q-nav-pill ${isCurrent ? 'current' : ''} ${isAtt ? 'attempted' : ''} ${isSkp ? 'skipped' : ''}`}
                  onClick={() => switchQuestion(idx)}
                  title={`Question ${idx + 1}: ${isAtt ? 'Answered' : isSkp ? 'Skipped' : 'Unanswered'}`}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          {/* Active Question Card */}
          {currentQ && (
            <div className="practice-question-card">
              <div className="question-card-header">
                <div>
                  <span className="question-indicator-label">
                    Question {currentQIndex + 1} of {activeSession.total_questions}
                  </span>
                </div>
                <div className="question-meta-chips">
                  <span className="meta-chip">{currentQ.round_type}</span>
                  {currentQ.topic && <span className="meta-chip">{currentQ.topic}</span>}
                  <span className={`meta-chip diff-${currentQ.difficulty.toLowerCase()}`}>
                    {currentQ.difficulty}
                  </span>
                  {currentQ.company_name && (
                    <span className="meta-chip" style={{ background: '#eff6ff', color: '#1d4ed8' }}>
                      {currentQ.company_name}
                    </span>
                  )}
                </div>
              </div>

              <div className="question-statement-text">{currentQ.question_text}</div>

              {/* Preparation Guidance Framework */}
              <div className="guidance-box">
                <div
                  className="guidance-header"
                  onClick={() => setIsGuidanceOpen(!isGuidanceOpen)}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Lightbulb size={16} color="#eab308" />
                    {isHRRound ? 'STAR Behavioral Framework Guidance' : 'Structured Problem-Solving Strategy'}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    {isGuidanceOpen ? 'Hide' : 'Show Tips'}
                  </span>
                </div>

                {isGuidanceOpen && (
                  <div className="guidance-content">
                    {isHRRound ? (
                      <>
                        <div className="star-card">
                          <span className="star-letter">S</span>
                          <span className="star-title">Situation</span>
                          <span className="star-desc">Set the scene and outline the context or project goal.</span>
                        </div>
                        <div className="star-card">
                          <span className="star-letter">T</span>
                          <span className="star-title">Task</span>
                          <span className="star-desc">Clarify your specific responsibility or challenge.</span>
                        </div>
                        <div className="star-card">
                          <span className="star-letter">A</span>
                          <span className="star-title">Action</span>
                          <span className="star-desc">Detail the exact steps and decisions YOU executed.</span>
                        </div>
                        <div className="star-card">
                          <span className="star-letter">R</span>
                          <span className="star-title">Result</span>
                          <span className="star-desc">Quantify the business outcome, learning, or impact.</span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="star-card">
                          <span className="star-letter" style={{ background: '#7c3aed' }}>1</span>
                          <span className="star-title">Clarify & Scope</span>
                          <span className="star-desc">Identify inputs, outputs, edge cases, and constraints.</span>
                        </div>
                        <div className="star-card">
                          <span className="star-letter" style={{ background: '#7c3aed' }}>2</span>
                          <span className="star-title">High-Level Approach</span>
                          <span className="star-desc">State the naive solution, then outline the optimized design.</span>
                        </div>
                        <div className="star-card">
                          <span className="star-letter" style={{ background: '#7c3aed' }}>3</span>
                          <span className="star-title">Walkthrough & Code</span>
                          <span className="star-desc">Implement clean logic or explain pseudocode line-by-line.</span>
                        </div>
                        <div className="star-card">
                          <span className="star-letter" style={{ background: '#7c3aed' }}>4</span>
                          <span className="star-title">Complexity Analysis</span>
                          <span className="star-desc">Explicitly state Time (Big-O) and Space complexity.</span>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* Student Answer Textarea */}
              <div className="answer-editor-box">
                <label style={{ fontSize: '0.88rem', fontWeight: 600, color: '#0f172a' }}>
                  Your Practice Answer (or Algorithm / Code Explanation)
                </label>
                <textarea
                  className="answer-textarea"
                  value={answerText}
                  onChange={handleAnswerChange}
                  placeholder={
                    isHRRound
                      ? 'Type your response here using the STAR format (Situation, Task, Action, Result)...'
                      : 'Write your technical explanation, SQL query, Python pseudocode, or algorithm walk-through...'
                  }
                />

                <div className="editor-bottom-bar">
                  <span>
                    Words: {answerText.trim() ? answerText.trim().split(/\s+/).length : 0} | Characters: {answerText.length}
                  </span>
                  <span className="autosave-status">
                    {autosaveStatus === 'saving' && (
                      <>
                        <RefreshCw size={12} className="spin" style={{ animation: 'spin 1s linear infinite' }} /> Saving...
                      </>
                    )}
                    {autosaveStatus === 'saved' && (
                      <>
                        <CheckCircle size={12} color="#059669" /> All changes autosaved
                      </>
                    )}
                    {autosaveStatus === 'error' && (
                      <span style={{ color: '#dc2626' }}>
                        <AlertCircle size={12} /> Autosave error
                      </span>
                    )}
                  </span>
                </div>
              </div>

              {/* Structured Self-Review & Reflection Accordion */}
              <div className="self-review-section">
                <div
                  className="self-review-header"
                  onClick={() => setIsSelfReviewOpen(!isSelfReviewOpen)}
                  style={{ cursor: 'pointer' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Award size={18} color="#2563eb" />
                    <span className="self-review-title">Self-Review & Reflection for this Question</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="self-review-disclaimer">Student Self-Assessment (1–5)</span>
                    <span style={{ fontSize: '0.8rem', color: '#2563eb', fontWeight: 600 }}>
                      {isSelfReviewOpen ? 'Collapse' : 'Expand Ratings'}
                    </span>
                  </div>
                </div>

                {isSelfReviewOpen && (
                  <>
                    <p style={{ fontSize: '0.8rem', color: '#64748b', fontStyle: 'italic' }}>
                      Rate your own response honestly to track personal growth. These are transparent self-assessment scores, not AI interviewer evaluations.
                    </p>

                    <div className="ratings-grid">
                      {criteriaToRender.map((crit) => {
                        const currentScore = selfRatings[crit.key] || 0;
                        return (
                          <div key={crit.key} className="criterion-rating-item">
                            <span className="criterion-label">{crit.label}</span>
                            <div className="rating-stars-row">
                              {[1, 2, 3, 4, 5].map((val) => (
                                <button
                                  key={val}
                                  type="button"
                                  className={`rating-star-btn ${val <= currentScore ? 'filled' : ''}`}
                                  onClick={() => handleRatingChange(crit.key, val)}
                                  title={`${crit.label}: ${val} / 5`}
                                >
                                  <Star size={18} fill={val <= currentScore ? '#eab308' : 'none'} />
                                </button>
                              ))}
                              {currentScore > 0 && (
                                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#0f172a', marginLeft: '4px' }}>
                                  {currentScore}/5
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="reflection-inputs-grid">
                      <div className="reflection-field">
                        <label>What went well in this answer?</label>
                        <textarea
                          value={reflection.went_well}
                          onChange={(e) => handleReflectionChange('went_well', e.target.value)}
                          placeholder="e.g. Delivered STAR structure smoothly, mentioned edge cases..."
                        />
                      </div>
                      <div className="reflection-field">
                        <label>What was difficult?</label>
                        <textarea
                          value={reflection.was_difficult}
                          onChange={(e) => handleReflectionChange('was_difficult', e.target.value)}
                          placeholder="e.g. Explaining space complexity, recalling specific metrics..."
                        />
                      </div>
                      <div className="reflection-field">
                        <label>What I need to learn or revise:</label>
                        <textarea
                          value={reflection.need_to_learn}
                          onChange={(e) => handleReflectionChange('need_to_learn', e.target.value)}
                          placeholder="e.g. Review SQL window functions, practice brevity..."
                        />
                      </div>
                      <div className="reflection-field">
                        <label>A better approach for next time:</label>
                        <textarea
                          value={reflection.better_approach}
                          onChange={(e) => handleReflectionChange('better_approach', e.target.value)}
                          placeholder="e.g. State conclusion first, use concrete examples..."
                        />
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Runner Bottom Action Bar */}
              <div className="runner-action-bar">
                <div className="runner-btn-group-left">
                  <button
                    className="runner-btn runner-btn-secondary"
                    disabled={currentQIndex === 0}
                    onClick={() => switchQuestion(currentQIndex - 1)}
                  >
                    <ChevronLeft size={16} /> Previous
                  </button>
                  <button
                    className="runner-btn runner-btn-skip"
                    onClick={handleSkipQuestion}
                  >
                    <SkipForward size={16} /> Skip Question
                  </button>
                </div>

                <div className="runner-btn-group-right">
                  <button
                    className="runner-btn runner-btn-secondary"
                    onClick={() => saveCurrentAnswer()}
                  >
                    <Save size={16} /> Save Answer
                  </button>

                  {currentQIndex < activeSession.total_questions - 1 ? (
                    <button
                      className="runner-btn runner-btn-primary"
                      onClick={() => switchQuestion(currentQIndex + 1)}
                    >
                      Next Question <ChevronRight size={16} />
                    </button>
                  ) : (
                    <button
                      className="runner-btn runner-btn-finish"
                      onClick={() => setShowFinishConfirm(true)}
                    >
                      Review & Complete Interview <CheckCircle size={16} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Finish Confirmation Modal */}
          {showFinishConfirm && (
            <div style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
              <div style={{ background: '#ffffff', borderRadius: '12px', padding: '1.75rem', maxWidth: '440px', width: '90%', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.75rem' }}>
                  Finish Mock Interview?
                </h3>
                <p style={{ fontSize: '0.9rem', color: '#64748b', lineHeight: 1.45, marginBottom: '1.25rem' }}>
                  Are you ready to finalize your practice session? We will compile your transparent performance summary report and save your reflections.
                </p>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                  <button
                    className="runner-btn runner-btn-secondary"
                    onClick={() => setShowFinishConfirm(false)}
                    disabled={isFinishing}
                  >
                    Continue Interview
                  </button>
                  <button
                    className="runner-btn runner-btn-finish"
                    onClick={handleFinishSession}
                    disabled={isFinishing}
                  >
                    {isFinishing ? 'Finalizing...' : 'Yes, Finish Interview'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* STAGE 3: SESSION SUMMARY & REPORT                                   */}
      {/* =================================================================== */}
      {activeTab === 'report' && (
        <div className="report-container">
          {reportLoading ? (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <RefreshCw size={28} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
              <p style={{ marginTop: '0.5rem', color: '#64748b' }}>Loading practice report...</p>
            </div>
          ) : reportData ? (
            <>
              {/* Report Header Card */}
              <div className="report-header-card">
                <div className="report-header-info">
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255, 255, 255, 0.2)', padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    <CheckCircle size={12} /> Practice Session Completed
                  </div>
                  <h1>{reportData.session_name}</h1>
                  <div className="report-header-meta">
                    <span>Round: {reportData.round_type}</span>
                    {reportData.target_company && (
                      <span>• Company: {reportData.target_company}</span>
                    )}
                    {reportData.target_role && (
                      <span>• Role: {reportData.target_role}</span>
                    )}
                    <span>• Duration: {reportData.duration_formatted}</span>
                  </div>
                </div>

                <div className="report-actions">
                  <button
                    className="report-btn report-btn-light"
                    onClick={() => setActiveTab('setup')}
                  >
                    <Sparkles size={16} /> New Session
                  </button>
                  <button
                    className="report-btn"
                    style={{ background: 'rgba(255, 255, 255, 0.2)', color: '#ffffff', border: '1px solid rgba(255, 255, 255, 0.3)' }}
                    onClick={() => setActiveTab('history')}
                  >
                    <Clock size={16} /> History
                  </button>
                </div>
              </div>

              {/* Stats Overview Grid */}
              <div className="report-stats-grid">
                <div className="report-stat-card">
                  <span className="report-stat-label">Total Questions</span>
                  <span className="report-stat-value">{reportData.total_questions}</span>
                </div>
                <div className="report-stat-card">
                  <span className="report-stat-label">Questions Attempted</span>
                  <span className="report-stat-value" style={{ color: '#047857' }}>
                    {reportData.questions_attempted}
                  </span>
                </div>
                <div className="report-stat-card">
                  <span className="report-stat-label">Questions Skipped</span>
                  <span className="report-stat-value" style={{ color: '#854d0e' }}>
                    {reportData.questions_skipped}
                  </span>
                </div>
                <div className="report-stat-card">
                  <span className="report-stat-label">Average Self-Assessment</span>
                  <span className="report-stat-value" style={{ color: '#2563eb' }}>
                    {reportData.scores_available && reportData.overall_average_score
                      ? `${reportData.overall_average_score} / 5.0`
                      : 'Not Rated'}
                  </span>
                </div>
              </div>

              {/* Criteria Scores & Insights Split */}
              <div className="report-insights-split">
                {/* Left: Criteria Score Breakdown */}
                <div className="criteria-card">
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a' }}>
                    Self-Assessment Criteria Breakdown
                  </h3>

                  {reportData.scores_available && Object.keys(reportData.criteria_averages).length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                      {Object.entries(reportData.criteria_averages).map(([critKey, score]) => {
                        const pct = (score / 5.0) * 100;
                        const label = critKey.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                        return (
                          <div key={critKey} className="score-bar-item">
                            <div className="score-bar-header">
                              <span>{label}</span>
                              <span style={{ fontWeight: 700, color: '#0f172a' }}>{score} / 5.0</span>
                            </div>
                            <div className="score-bar-track">
                              <div className="score-bar-fill" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p style={{ fontSize: '0.88rem', color: '#64748b', fontStyle: 'italic' }}>
                      You did not submit ratings for this session. Complete the 1–5 self-review in future sessions to track criteria mastery.
                    </p>
                  )}
                </div>

                {/* Right: Highlights & Areas for Improvement */}
                <div className="insights-card">
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a' }}>
                    Strengths & Areas for Improvement
                  </h3>

                  <div className="insight-block strengths">
                    <span className="insight-title">
                      <CheckCircle size={16} /> Strongest Self-Assessed Areas
                    </span>
                    {reportData.strongest_areas?.length > 0 ? (
                      <ul className="insight-list">
                        {reportData.strongest_areas.map((area, i) => (
                          <li key={i}>{area}</li>
                        ))}
                      </ul>
                    ) : (
                      <span style={{ fontSize: '0.82rem', color: '#15803d' }}>
                        Ratings completed uniformly or pending.
                      </span>
                    )}
                  </div>

                  <div className="insight-block improvements">
                    <span className="insight-title">
                      <AlertTriangle size={16} /> Focus Areas for Practice
                    </span>
                    {reportData.areas_for_improvement?.length > 0 ? (
                      <ul className="insight-list">
                        {reportData.areas_for_improvement.map((area, i) => (
                          <li key={i}>{area}</li>
                        ))}
                      </ul>
                    ) : (
                      <span style={{ fontSize: '0.82rem', color: '#b45309' }}>
                        No specific weaknesses flagged below threshold.
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Actionable Next Steps */}
              {reportData.recommendations?.length > 0 && (
                <div className="recommendations-box">
                  <div className="recommendations-title">
                    <Sparkles size={18} /> Actionable Next Steps
                  </div>
                  <ul className="recommendations-list">
                    {reportData.recommendations.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                  <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.5rem', fontStyle: 'italic' }}>
                    Transparency notice: This report summarizes student self-assessment and session activity. It does not measure actual hiring probability or guaranteed interview outcomes.
                  </p>
                </div>
              )}

              {/* Q&A Accordion Review */}
              <div className="report-answers-section">
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a' }}>
                  Question-by-Question Review
                </h3>

                {reportData.answers?.map((ans, idx) => (
                  <div key={ans.id || idx} className="report-qa-card">
                    <div className="report-qa-header">
                      <div>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#2563eb', textTransform: 'uppercase' }}>
                          Question {idx + 1} • {ans.round_type}
                        </span>
                        <div className="report-qa-question">{ans.question_text}</div>
                      </div>
                      <div>
                        {ans.is_attempted ? (
                          <span className="status-badge completed">Answered</span>
                        ) : ans.is_skipped ? (
                          <span className="status-badge abandoned">Skipped</span>
                        ) : (
                          <span className="status-badge in-progress">Unanswered</span>
                        )}
                      </div>
                    </div>

                    <div>
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>
                        Your Answer:
                      </span>
                      <div className="report-qa-answer-block">
                        {ans.answer_text ? ans.answer_text : <span style={{ color: '#94a3b8' }}>[No answer provided]</span>}
                      </div>
                    </div>

                    {ans.expected_answer && (
                      <div>
                        <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>
                          Key Guidance / Expected Talking Points:
                        </span>
                        <div className="report-qa-answer-block" style={{ background: '#f0fdf4', borderColor: '#bbf7d0', color: '#166534' }}>
                          {ans.expected_answer}
                        </div>
                      </div>
                    )}

                    {ans.self_ratings && Object.keys(ans.self_ratings).length > 0 && (
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.25rem' }}>
                        {Object.entries(ans.self_ratings).map(([k, v]) => (
                          <span key={k} style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.75rem', color: '#1d4ed8', fontWeight: 600 }}>
                            {k.replace(/_/g, ' ')}: {v}/5
                          </span>
                        ))}
                      </div>
                    )}

                    {(ans.went_well || ans.was_difficult || ans.need_to_learn || ans.better_approach) && (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem', background: '#f8fafc', padding: '0.65rem', borderRadius: '6px', fontSize: '0.8rem' }}>
                        {ans.went_well && <div><strong>Went well:</strong> {ans.went_well}</div>}
                        {ans.was_difficult && <div><strong>Difficult:</strong> {ans.was_difficult}</div>}
                        {ans.need_to_learn && <div><strong>Need to learn:</strong> {ans.need_to_learn}</div>}
                        {ans.better_approach && <div><strong>Better approach:</strong> {ans.better_approach}</div>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
              <p>No report loaded. Complete a practice session to view your performance summary.</p>
            </div>
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* PRACTICE HISTORY VIEW                                               */}
      {/* =================================================================== */}
      {activeTab === 'history' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Filter Bar */}
          <div className="history-filter-bar">
            <input
              type="text"
              className="history-search-input"
              placeholder="Search session name, company, or role..."
              value={historySearch}
              onChange={(e) => setHistorySearch(e.target.value)}
            />

            <select
              value={historyStatusFilter}
              onChange={(e) => setHistoryStatusFilter(e.target.value)}
              style={{ padding: '0.55rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
            >
              <option value="All">All Statuses</option>
              <option value="Completed">Completed</option>
              <option value="In Progress">In Progress</option>
              <option value="Abandoned">Abandoned</option>
            </select>

            <select
              value={historyRoundFilter}
              onChange={(e) => setHistoryRoundFilter(e.target.value)}
              style={{ padding: '0.55rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
            >
              <option value="All">All Rounds</option>
              {ROUND_TYPES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          {/* History Cards Grid */}
          {historyLoading ? (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <RefreshCw size={24} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
              <p style={{ marginTop: '0.5rem', color: '#64748b' }}>Loading history...</p>
            </div>
          ) : historyList.length > 0 ? (
            <div className="history-grid">
              {historyList.map((session) => {
                const isCompleted = session.status === 'Completed';
                const isInProgress = session.status === 'In Progress';
                return (
                  <div key={session.id} className="history-card">
                    <div className="history-card-top">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                        <span className="history-card-title">{session.session_name}</span>
                        <span className={`status-badge ${session.status.toLowerCase().replace(/\s+/g, '-')}`}>
                          {session.status}
                        </span>
                      </div>
                      <div className="history-card-badges">
                        <span className="meta-chip">{session.round_type}</span>
                        <span className="meta-chip">{session.difficulty}</span>
                        {session.target_company && (
                          <span className="meta-chip" style={{ background: '#f5f3ff', color: '#6d28d9' }}>
                            {session.target_company}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="history-card-metrics">
                      <span>Questions: {session.attempted_count} / {session.total_questions} answered</span>
                      <span>
                        Rating: {session.average_score ? `${session.average_score}/5` : 'None'}
                      </span>
                    </div>

                    <div className="history-card-actions">
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                        {session.created_at ? new Date(session.created_at).toLocaleDateString() : ''}
                      </span>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {isCompleted && (
                          <button
                            className="runner-btn runner-btn-secondary"
                            style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
                            onClick={() => handleReviewHistorySession(session.id)}
                          >
                            <FileText size={14} /> Review
                          </button>
                        )}
                        {isInProgress && (
                          <button
                            className="runner-btn runner-btn-primary"
                            style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
                            onClick={() => handleResumeHistorySession(session.id)}
                          >
                            <Play size={14} /> Resume
                          </button>
                        )}
                        <button
                          className="timer-pause-btn"
                          style={{ color: '#ef4444' }}
                          title="Delete practice session"
                          onClick={() => handleDeleteSession(session.id)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-history-state">
              <div className="empty-history-icon">
                <Clock size={28} />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a' }}>
                No Practice Sessions Yet
              </h3>
              <p style={{ fontSize: '0.9rem', color: '#64748b', maxWidth: '400px' }}>
                Create your first mock interview session to practice questions, time your responses, and track improvement over time.
              </p>
              <button
                className="start-session-btn"
                style={{ width: 'auto', padding: '0.65rem 1.25rem', fontSize: '0.9rem' }}
                onClick={() => setActiveTab('setup')}
              >
                <Sparkles size={16} /> Configure First Session
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
