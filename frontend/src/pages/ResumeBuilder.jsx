import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  FileText,
  Save,
  Copy,
  Trash2,
  Plus,
  Download,
  Printer,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Briefcase,
  RefreshCw
} from 'lucide-react';
import {
  getResumes,
  getResumeById,
  createResume,
  updateResume,
  duplicateResume,
  deleteResume,
  reviewResume,
  tailorResume,
  getSampleResume,
  getDocxExportUrl,
  getApplications
} from '../services/api';
import '../styles/resume.css';

// Default target roles for quick selection
const TARGET_ROLES = [
  'General Software Engineering',
  'Frontend Developer',
  'Full-Stack Developer',
  'Python Developer',
  'Data Science Intern',
  'Backend Engineer',
  'Mobile App Developer'
];

// Initial blank resume structure
const BLANK_RESUME = {
  title: 'Untitled Resume Draft',
  target_role: 'Full-Stack Developer',
  target_job_id: null,
  template_id: 'ats-classic',
  contact_info: {
    full_name: '',
    email: '',
    phone: '',
    location: '',
    linkedin_url: '',
    github_url: '',
    portfolio_url: ''
  },
  summary: '',
  skills: [
    { category: 'Programming Languages', items: ['Python', 'JavaScript'] },
    { category: 'Frontend Technologies', items: ['React', 'HTML5', 'CSS3'] },
    { category: 'Backend & Databases', items: ['FastAPI', 'SQLite', 'REST APIs'] },
    { category: 'Developer Tools', items: ['Git', 'GitHub', 'VS Code'] }
  ],
  education: [
    {
      institution: '',
      degree: 'Bachelor of Technology',
      field_of_study: 'Computer Science and Engineering',
      start_date: '2022',
      graduation_date: '2026',
      gpa: '',
      coursework: 'Data Structures, Algorithms, DBMS, Operating Systems, Web Technologies'
    }
  ],
  projects: [
    {
      title: '',
      description: '',
      technologies: [],
      start_date: '',
      end_date: '',
      github_url: '',
      live_url: '',
      bullets: ['']
    }
  ],
  experience: [],
  additional_sections: {
    certifications: [],
    achievements: [],
    leadership: [],
    languages: []
  },
  section_config: {
    order: ['summary', 'skills', 'education', 'projects', 'experience', 'certifications', 'achievements'],
    enabled: {
      summary: true,
      skills: true,
      education: true,
      projects: true,
      experience: false,
      certifications: true,
      achievements: false,
      leadership: false,
      languages: false
    }
  }
};

export default function ResumeBuilder() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlResumeId = searchParams.get('id');
  const urlInitialTab = searchParams.get('tab');

  // Resume state
  const [resumesList, setResumesList] = useState([]);
  const [currentResume, setCurrentResume] = useState(BLANK_RESUME);
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('All changes saved');

  // Job options for tailoring
  const [savedJobs, setSavedJobs] = useState([]);

  // Active tabs
  const [activeEditorTab, setActiveEditorTab] = useState('contact');
  const [activePreviewTab, setActivePreviewTab] = useState(urlInitialTab === 'review' ? 'review' : 'preview');
  const [mobileView, setMobileView] = useState('editor'); // 'editor' | 'preview' | 'review' | 'tailor'

  // Quality Review and Tailoring data
  const [reviewData, setReviewData] = useState(null);
  const [tailorData, setTailorData] = useState(null);
  const [isReviewLoading, setIsReviewLoading] = useState(false);
  const [isTailorLoading, setIsTailorLoading] = useState(false);

  // Modals
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [sampleModalOpen, setSampleModalOpen] = useState(false);
  const [errorBanner, setErrorBanner] = useState('');

  // Skill category tag input temp state
  const [newTagInput, setNewTagInput] = useState({});

  // 1. Initial Load: Resumes & Jobs
  useEffect(() => {
    loadResumesAndJobs();
  }, []);

  // When resumesList or URL changes, select target resume
  useEffect(() => {
    if (resumesList.length > 0) {
      if (urlResumeId) {
        const found = resumesList.find((r) => r.id === parseInt(urlResumeId, 10));
        if (found) {
          fetchSingleResume(found.id);
          return;
        }
      }
      // Default to first resume
      if (!currentResume.id) {
        fetchSingleResume(resumesList[0].id);
      }
    }
  }, [urlResumeId, resumesList]);

  async function loadResumesAndJobs() {
    try {
      const [resumesRes, jobsRes] = await Promise.all([
        getResumes(),
        getApplications()
      ]);

      if (resumesRes.ok && resumesRes.data) {
        setResumesList(resumesRes.data);
      }
      if (jobsRes.ok && jobsRes.data) {
        setSavedJobs(jobsRes.data);
      }
    } catch (err) {
      setErrorBanner('Failed to connect to backend server. Please check connection.');
    }
  }

  async function fetchSingleResume(id) {
    try {
      const res = await getResumeById(id);
      if (res.ok && res.data) {
        setCurrentResume(res.data);
        setIsDirty(false);
        setSaveMessage('Saved');
        // If reviewing, fetch review data
        triggerReview(res.data.id);
        if (res.data.target_job_id) {
          triggerTailor(res.data.id, res.data.target_job_id);
        } else {
          setTailorData(null);
        }
      }
    } catch (err) {
      setErrorBanner('Could not load requested resume draft.');
    }
  }

  // 2. Draft Management Actions
  async function handleCreateNewDraft() {
    try {
      setIsSaving(true);
      const newDraftData = {
        ...BLANK_RESUME,
        title: `Resume Draft #${resumesList.length + 1}`
      };
      const res = await createResume(newDraftData);
      if (res.ok && res.data) {
        setResumesList([res.data, ...resumesList]);
        setCurrentResume(res.data);
        setSearchParams({ id: res.data.id });
        setIsDirty(false);
        setSaveMessage('Saved');
        triggerReview(res.data.id);
      }
    } catch (err) {
      setErrorBanner('Error creating new resume draft.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSaveCurrentResume() {
    if (!currentResume.id) {
      // Create first
      handleCreateNewDraft();
      return;
    }

    try {
      setIsSaving(true);
      const res = await updateResume(currentResume.id, currentResume);
      if (res.ok && res.data) {
        setCurrentResume(res.data);
        setIsDirty(false);
        setSaveMessage('Saved just now');
        // Update list title/role
        setResumesList((prev) =>
          prev.map((r) => (r.id === res.data.id ? res.data : r))
        );
        // Refresh review
        triggerReview(res.data.id);
        if (res.data.target_job_id) {
          triggerTailor(res.data.id, res.data.target_job_id);
        }
      }
    } catch (err) {
      setErrorBanner('Failed to save resume changes.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDuplicateDraft() {
    if (!currentResume.id) return;
    try {
      setIsSaving(true);
      const res = await duplicateResume(currentResume.id);
      if (res.ok && res.data) {
        setResumesList([res.data, ...resumesList]);
        setCurrentResume(res.data);
        setSearchParams({ id: res.data.id });
        setIsDirty(false);
        triggerReview(res.data.id);
      }
    } catch (err) {
      setErrorBanner('Failed to duplicate resume.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteDraft() {
    if (!currentResume.id) return;
    try {
      const res = await deleteResume(currentResume.id);
      if (res.ok) {
        const remaining = resumesList.filter((r) => r.id !== currentResume.id);
        setResumesList(remaining);
        setDeleteModalOpen(false);
        if (remaining.length > 0) {
          fetchSingleResume(remaining[0].id);
          setSearchParams({ id: remaining[0].id });
        } else {
          setCurrentResume(BLANK_RESUME);
        }
      }
    } catch (err) {
      setErrorBanner('Failed to delete resume draft.');
    }
  }

  async function handleLoadSampleResume() {
    try {
      setIsSaving(true);
      const res = await getSampleResume('frontend');
      if (res.ok && res.data) {
        const createRes = await createResume({
          ...res.data,
          title: 'Sample: Frontend Developer Resume'
        });
        if (createRes.ok && createRes.data) {
          setResumesList([createRes.data, ...resumesList]);
          setCurrentResume(createRes.data);
          setSearchParams({ id: createRes.data.id });
          setIsDirty(false);
          setSampleModalOpen(false);
          triggerReview(createRes.data.id);
        }
      }
    } catch (err) {
      setErrorBanner('Failed to load sample resume.');
    } finally {
      setIsSaving(false);
    }
  }

  // 3. Review and Tailoring Calls
  async function triggerReview(resumeId) {
    if (!resumeId) return;
    setIsReviewLoading(true);
    try {
      const res = await reviewResume(resumeId);
      if (res.ok && res.data) {
        setReviewData(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsReviewLoading(false);
    }
  }

  async function triggerTailor(resumeId, jobId) {
    if (!resumeId || !jobId) return;
    setIsTailorLoading(true);
    try {
      const res = await tailorResume(resumeId, jobId);
      if (res.ok && res.data) {
        setTailorData(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsTailorLoading(false);
    }
  }

  function handleSelectTargetJob(jobIdStr) {
    const jId = jobIdStr ? parseInt(jobIdStr, 10) : null;
    const updated = { ...currentResume, target_job_id: jId };
    setCurrentResume(updated);
    setIsDirty(true);
    setSaveMessage('Unsaved changes');

    if (jId && currentResume.id) {
      triggerTailor(currentResume.id, jId);
    } else {
      setTailorData(null);
    }
  }

  // 4. Form Change Helpers
  function handleContactChange(field, value) {
    setCurrentResume((prev) => ({
      ...prev,
      contact_info: {
        ...prev.contact_info,
        [field]: value
      }
    }));
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleSummaryChange(val) {
    setCurrentResume((prev) => ({ ...prev, summary: val }));
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  // Skills
  function handleAddSkillTag(categoryIndex, tag) {
    if (!tag || !tag.trim()) return;
    const cleaned = tag.trim();
    setCurrentResume((prev) => {
      const copySkills = [...prev.skills];
      if (!copySkills[categoryIndex].items.includes(cleaned)) {
        copySkills[categoryIndex].items.push(cleaned);
      }
      return { ...prev, skills: copySkills };
    });
    setNewTagInput((prev) => ({ ...prev, [categoryIndex]: '' }));
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleRemoveSkillTag(categoryIndex, tagIndex) {
    setCurrentResume((prev) => {
      const copySkills = [...prev.skills];
      copySkills[categoryIndex].items.splice(tagIndex, 1);
      return { ...prev, skills: copySkills };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleAddSkillCategory() {
    setCurrentResume((prev) => ({
      ...prev,
      skills: [...prev.skills, { category: 'New Skill Category', items: [] }]
    }));
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleRemoveSkillCategory(catIndex) {
    setCurrentResume((prev) => {
      const copySkills = [...prev.skills];
      copySkills.splice(catIndex, 1);
      return { ...prev, skills: copySkills };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  // Education
  function handleEducationChange(index, field, value) {
    setCurrentResume((prev) => {
      const copyEdu = [...prev.education];
      copyEdu[index] = { ...copyEdu[index], [field]: value };
      return { ...prev, education: copyEdu };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleAddEducation() {
    setCurrentResume((prev) => ({
      ...prev,
      education: [
        ...prev.education,
        {
          institution: '',
          degree: 'Bachelor of Technology',
          field_of_study: 'Computer Science and Engineering',
          start_date: '2022',
          graduation_date: '2026',
          gpa: '',
          coursework: ''
        }
      ]
    }));
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleRemoveEducation(index) {
    setCurrentResume((prev) => {
      const copyEdu = [...prev.education];
      copyEdu.splice(index, 1);
      return { ...prev, education: copyEdu };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  // Projects
  function handleProjectChange(index, field, value) {
    setCurrentResume((prev) => {
      const copyProj = [...prev.projects];
      copyProj[index] = { ...copyProj[index], [field]: value };
      return { ...prev, projects: copyProj };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleAddProject() {
    setCurrentResume((prev) => ({
      ...prev,
      projects: [
        ...prev.projects,
        {
          title: 'New Technical Project',
          description: '',
          technologies: [],
          start_date: '',
          end_date: '',
          github_url: '',
          live_url: '',
          bullets: ['Developed feature using technology, improving outcome.']
        }
      ]
    }));
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleRemoveProject(index) {
    setCurrentResume((prev) => {
      const copyProj = [...prev.projects];
      copyProj.splice(index, 1);
      return { ...prev, projects: copyProj };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleProjectBulletChange(projIndex, bulletIndex, value) {
    setCurrentResume((prev) => {
      const copyProj = [...prev.projects];
      const copyBullets = [...(copyProj[projIndex].bullets || [])];
      copyBullets[bulletIndex] = value;
      copyProj[projIndex].bullets = copyBullets;
      return { ...prev, projects: copyProj };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleAddProjectBullet(projIndex) {
    setCurrentResume((prev) => {
      const copyProj = [...prev.projects];
      const copyBullets = [...(copyProj[projIndex].bullets || [])];
      copyBullets.push('');
      copyProj[projIndex].bullets = copyBullets;
      return { ...prev, projects: copyProj };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleRemoveProjectBullet(projIndex, bulletIndex) {
    setCurrentResume((prev) => {
      const copyProj = [...prev.projects];
      const copyBullets = [...(copyProj[projIndex].bullets || [])];
      copyBullets.splice(bulletIndex, 1);
      copyProj[projIndex].bullets = copyBullets;
      return { ...prev, projects: copyProj };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  // Experience
  function handleExperienceChange(index, field, value) {
    setCurrentResume((prev) => {
      const copyExp = [...prev.experience];
      copyExp[index] = { ...copyExp[index], [field]: value };
      return { ...prev, experience: copyExp };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleAddExperience() {
    setCurrentResume((prev) => {
      const copyConfig = { ...prev.section_config };
      copyConfig.enabled = { ...copyConfig.enabled, experience: true };
      return {
        ...prev,
        section_config: copyConfig,
        experience: [
          ...prev.experience,
          {
            organization: 'Company / Organization',
            job_title: 'Software Engineering Intern',
            employment_type: 'Internship',
            start_date: 'May 2024',
            end_date: 'July 2024',
            location: '',
            bullets: ['Built responsive features and collaborated with senior engineers.']
          }
        ]
      };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleRemoveExperience(index) {
    setCurrentResume((prev) => {
      const copyExp = [...prev.experience];
      copyExp.splice(index, 1);
      return { ...prev, experience: copyExp };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleExperienceBulletChange(expIndex, bulletIndex, value) {
    setCurrentResume((prev) => {
      const copyExp = [...prev.experience];
      const copyBullets = [...(copyExp[expIndex].bullets || [])];
      copyBullets[bulletIndex] = value;
      copyExp[expIndex].bullets = copyBullets;
      return { ...prev, experience: copyExp };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleAddExperienceBullet(expIndex) {
    setCurrentResume((prev) => {
      const copyExp = [...prev.experience];
      const copyBullets = [...(copyExp[expIndex].bullets || [])];
      copyBullets.push('');
      copyExp[expIndex].bullets = copyBullets;
      return { ...prev, experience: copyExp };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  function handleRemoveExperienceBullet(expIndex, bulletIndex) {
    setCurrentResume((prev) => {
      const copyExp = [...prev.experience];
      const copyBullets = [...(copyExp[expIndex].bullets || [])];
      copyBullets.splice(bulletIndex, 1);
      copyExp[expIndex].bullets = copyBullets;
      return { ...prev, experience: copyExp };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  // Additional sections toggle
  function handleToggleSection(sectionKey) {
    setCurrentResume((prev) => {
      const copyConfig = { ...prev.section_config };
      const currentVal = copyConfig.enabled?.[sectionKey] || false;
      copyConfig.enabled = { ...copyConfig.enabled, [sectionKey]: !currentVal };
      return { ...prev, section_config: copyConfig };
    });
    setIsDirty(true);
    setSaveMessage('Unsaved changes');
  }

  // 5. Validation Check
  const contactInfo = currentResume.contact_info || {};
  const isEmailValid = !contactInfo.email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactInfo.email);
  const isLinkedInValid = !contactInfo.linkedin_url || /linkedin\.com/i.test(contactInfo.linkedin_url) || /^https?:\/\//i.test(contactInfo.linkedin_url);
  const isGitHubValid = !contactInfo.github_url || /github\.com/i.test(contactInfo.github_url) || /^https?:\/\//i.test(contactInfo.github_url);

  // 6. Print PDF and Download DOCX
  function handlePrintPdf() {
    window.print();
  }

  function handleDownloadDocx() {
    if (!currentResume.id) {
      alert('Please save the resume draft first before exporting to DOCX.');
      return;
    }
    const url = getDocxExportUrl(currentResume.id);
    window.open(url, '_blank');
  }

  return (
    <div className="resume-page-container">
      {/* Top Banner Errors */}
      {errorBanner && (
        <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', color: '#dc2626', padding: '0.75rem 1rem', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{errorBanner}</span>
          <button onClick={() => setErrorBanner('')} style={{ fontWeight: 'bold' }}>×</button>
        </div>
      )}

      {/* Top Controls Bar */}
      <div className="resume-topbar">
        <div className="resume-topbar-left">
          {/* Draft Select */}
          <div className="resume-draft-select-group">
            <select
              className="resume-draft-select"
              value={currentResume.id || ''}
              onChange={(e) => {
                const id = parseInt(e.target.value, 10);
                if (id) {
                  fetchSingleResume(id);
                  setSearchParams({ id });
                }
              }}
            >
              {resumesList.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title} {r.target_role ? `(${r.target_role})` : ''}
                </option>
              ))}
              {resumesList.length === 0 && <option value="">Draft (Unsaved)</option>}
            </select>

            {/* Resume Title Rename */}
            <input
              type="text"
              className="resume-title-input"
              value={currentResume.title || ''}
              onChange={(e) => {
                setCurrentResume({ ...currentResume, title: e.target.value });
                setIsDirty(true);
                setSaveMessage('Unsaved changes');
              }}
              placeholder="e.g. Frontend Developer Resume"
            />
          </div>

          {/* Target Role Selector */}
          <select
            className="resume-role-select"
            value={currentResume.target_role || ''}
            onChange={(e) => {
              setCurrentResume({ ...currentResume, target_role: e.target.value });
              setIsDirty(true);
              setSaveMessage('Unsaved changes');
            }}
          >
            {TARGET_ROLES.map((role) => (
              <option key={role} value={role}>
                Target: {role}
              </option>
            ))}
          </select>

          {/* Target Job Selector */}
          <select
            className="resume-job-select"
            value={currentResume.target_job_id || ''}
            onChange={(e) => handleSelectTargetJob(e.target.value)}
          >
            <option value="">No Target Job (General ATS Resume)</option>
            {savedJobs.map((j) => (
              <option key={j.id} value={j.id}>
                Tailor: {j.company_name} — {j.job_title}
              </option>
            ))}
          </select>

          {/* Save Status Indicator */}
          <div className={`resume-save-status ${isDirty ? 'unsaved' : 'saved'}`}>
            {isDirty ? <AlertCircle size={14} /> : <CheckCircle2 size={14} />}
            <span>{isSaving ? 'Saving...' : saveMessage}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="resume-topbar-actions">
          <button
            className="btn-resume btn-resume-primary"
            onClick={handleSaveCurrentResume}
            disabled={isSaving}
          >
            <Save size={16} />
            <span>{isSaving ? 'Saving...' : 'Save Draft'}</span>
          </button>

          <button
            className="btn-resume btn-resume-outline"
            onClick={handleCreateNewDraft}
            title="Create a new blank resume version"
          >
            <Plus size={16} />
            <span>New</span>
          </button>

          <button
            className="btn-resume btn-resume-outline"
            onClick={handleDuplicateDraft}
            disabled={!currentResume.id}
            title="Duplicate this resume draft into a role-specific copy"
          >
            <Copy size={16} />
            <span>Duplicate</span>
          </button>

          <button
            className="btn-resume btn-resume-outline"
            onClick={handlePrintPdf}
            title="Print or save clean, selectable ATS PDF"
          >
            <Printer size={16} />
            <span>Export PDF</span>
          </button>

          <button
            className="btn-resume btn-resume-outline"
            onClick={handleDownloadDocx}
            disabled={!currentResume.id}
            title="Download ATS-compliant Word document"
          >
            <Download size={16} />
            <span>Export DOCX</span>
          </button>

          <button
            className="btn-resume btn-resume-outline"
            onClick={() => setSampleModalOpen(true)}
            title="Load sample template data"
          >
            <Sparkles size={16} />
            <span>Sample</span>
          </button>

          {currentResume.id && (
            <button
              className="btn-resume btn-resume-danger"
              onClick={() => setDeleteModalOpen(true)}
              title="Delete this resume draft"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Mobile Screen Switcher */}
      <div className="resume-mobile-switcher">
        <button
          className={mobileView === 'editor' ? 'active' : ''}
          onClick={() => setMobileView('editor')}
        >
          Editor
        </button>
        <button
          className={mobileView === 'preview' ? 'active' : ''}
          onClick={() => {
            setMobileView('preview');
            setActivePreviewTab('preview');
          }}
        >
          Preview
        </button>
        <button
          className={mobileView === 'review' ? 'active' : ''}
          onClick={() => {
            setMobileView('review');
            setActivePreviewTab('review');
            if (currentResume.id) triggerReview(currentResume.id);
          }}
        >
          ATS Review
        </button>
        {currentResume.target_job_id && (
          <button
            className={mobileView === 'tailor' ? 'active' : ''}
            onClick={() => {
              setMobileView('tailor');
              setActivePreviewTab('tailor');
              if (currentResume.id) triggerTailor(currentResume.id, currentResume.target_job_id);
            }}
          >
            Tailor
          </button>
        )}
      </div>

      {/* Main Workspace: Dual Split Pane */}
      <div className="resume-workspace">
        {/* ====================================================================
            LEFT PANE: Multi-Section Editor
            ==================================================================== */}
        <div className={`resume-editor-pane ${mobileView !== 'editor' ? 'hide-mobile' : ''}`}>
          {/* Section Navigation Tabs */}
          <div className="resume-editor-tabs">
            <button
              className={`resume-tab-btn ${activeEditorTab === 'contact' ? 'active' : ''}`}
              onClick={() => setActiveEditorTab('contact')}
            >
              Contact
            </button>
            <button
              className={`resume-tab-btn ${activeEditorTab === 'summary' ? 'active' : ''}`}
              onClick={() => setActiveEditorTab('summary')}
            >
              Summary
            </button>
            <button
              className={`resume-tab-btn ${activeEditorTab === 'skills' ? 'active' : ''}`}
              onClick={() => setActiveEditorTab('skills')}
            >
              Skills
            </button>
            <button
              className={`resume-tab-btn ${activeEditorTab === 'education' ? 'active' : ''}`}
              onClick={() => setActiveEditorTab('education')}
            >
              Education
            </button>
            <button
              className={`resume-tab-btn ${activeEditorTab === 'projects' ? 'active' : ''}`}
              onClick={() => setActiveEditorTab('projects')}
            >
              Projects ({currentResume.projects?.length || 0})
            </button>
            <button
              className={`resume-tab-btn ${activeEditorTab === 'experience' ? 'active' : ''}`}
              onClick={() => setActiveEditorTab('experience')}
            >
              Experience ({currentResume.experience?.length || 0})
            </button>
            <button
              className={`resume-tab-btn ${activeEditorTab === 'additional' ? 'active' : ''}`}
              onClick={() => setActiveEditorTab('additional')}
            >
              Sections
            </button>
          </div>

          {/* Section 1: Contact Information */}
          {activeEditorTab === 'contact' && (
            <div className="resume-section-body">
              <div className="resume-section-header">
                <div>
                  <h3 className="resume-section-title">Contact Details</h3>
                  <p className="resume-section-desc">
                    Standard header placed directly in the document body. Automated ATS parsers read this sequentially.
                  </p>
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label className="form-label">Full Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={contactInfo.full_name || ''}
                    onChange={(e) => handleContactChange('full_name', e.target.value)}
                    placeholder="e.g. Alex Johnson"
                  />
                  {!contactInfo.full_name && (
                    <span className="form-error">Name is required for ATS parsing.</span>
                  )}
                </div>

                <div className="form-group">
                  <label className="form-label">Professional Email *</label>
                  <input
                    type="email"
                    className={`form-input ${!isEmailValid ? 'invalid' : ''}`}
                    value={contactInfo.email || ''}
                    onChange={(e) => handleContactChange('email', e.target.value)}
                    placeholder="e.g. alex.johnson@email.com"
                  />
                  {!isEmailValid && (
                    <span className="form-error">Please enter a valid email address.</span>
                  )}
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label className="form-label">Phone Number</label>
                  <input
                    type="tel"
                    className="form-input"
                    value={contactInfo.phone || ''}
                    onChange={(e) => handleContactChange('phone', e.target.value)}
                    placeholder="e.g. +1 (555) 019-2834"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Current Location (City, State / Country)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={contactInfo.location || ''}
                    onChange={(e) => handleContactChange('location', e.target.value)}
                    placeholder="e.g. San Jose, CA (or Bangalore, India)"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">LinkedIn Profile URL</label>
                <input
                  type="url"
                  className={`form-input ${!isLinkedInValid ? 'invalid' : ''}`}
                  value={contactInfo.linkedin_url || ''}
                  onChange={(e) => handleContactChange('linkedin_url', e.target.value)}
                  placeholder="https://linkedin.com/in/alexjohnson"
                />
                {!isLinkedInValid && (
                  <span className="form-error">Provide a valid LinkedIn URL (e.g., linkedin.com/in/username).</span>
                )}
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label className="form-label">GitHub URL</label>
                  <input
                    type="url"
                    className={`form-input ${!isGitHubValid ? 'invalid' : ''}`}
                    value={contactInfo.github_url || ''}
                    onChange={(e) => handleContactChange('github_url', e.target.value)}
                    placeholder="https://github.com/alexjohnson"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Portfolio / Website URL</label>
                  <input
                    type="url"
                    className="form-input"
                    value={contactInfo.portfolio_url || ''}
                    onChange={(e) => handleContactChange('portfolio_url', e.target.value)}
                    placeholder="https://alexjohnson.dev"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Section 2: Professional Summary */}
          {activeEditorTab === 'summary' && (
            <div className="resume-section-body">
              <div className="resume-section-header">
                <div>
                  <h3 className="resume-section-title">Professional Summary</h3>
                  <p className="resume-section-desc">
                    A concise 2-3 sentence overview highlighting your core strengths, target role, and verified skills.
                  </p>
                </div>
              </div>

              <div className="bullet-guidance-box">
                <span className="bullet-formula-tag">Summary Writing Guidance:</span>
                <span>
                  Entry-level applicants should state their degree, primary technical focus (e.g., Python/React), and enthusiasm for building high-quality software. Avoid buzzwords like "hardworking guru" or unverified claims.
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <span>Summary Content</span>
                  <span className="form-hint">{currentResume.summary?.length || 0} characters</span>
                </label>
                <textarea
                  className="form-textarea"
                  rows={5}
                  value={currentResume.summary || ''}
                  onChange={(e) => handleSummaryChange(e.target.value)}
                  placeholder="e.g. Adaptable Computer Science graduate with hands-on experience in full-stack web development using React, FastAPI, and PostgreSQL. Proven ability to design maintainable REST APIs, implement intuitive user interfaces, and collaborate effectively in Agile team environments."
                />
              </div>
            </div>
          )}

          {/* Section 3: Technical Skills */}
          {activeEditorTab === 'skills' && (
            <div className="resume-section-body">
              <div className="resume-section-header">
                <div>
                  <h3 className="resume-section-title">Categorized Technical Skills</h3>
                  <p className="resume-section-desc">
                    Group skills logically into categories so ATS parsers match keywords and recruiters quickly evaluate domain fit.
                  </p>
                </div>
                <button className="btn-resume btn-resume-outline" onClick={handleAddSkillCategory}>
                  <Plus size={14} /> Add Category
                </button>
              </div>

              {(currentResume.skills || []).map((cat, catIdx) => (
                <div key={catIdx} className="skills-category-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <input
                      type="text"
                      className="form-input"
                      style={{ fontWeight: 'bold', width: '70%' }}
                      value={cat.category}
                      onChange={(e) => {
                        const copy = [...currentResume.skills];
                        copy[catIdx].category = e.target.value;
                        setCurrentResume({ ...currentResume, skills: copy });
                        setIsDirty(true);
                      }}
                      placeholder="Category Name"
                    />
                    <button
                      className="btn-icon-control danger"
                      onClick={() => handleRemoveSkillCategory(catIdx)}
                      title="Remove category"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  {/* Tag Pills */}
                  <div className="tags-wrapper">
                    {(cat.items || []).map((tag, tagIdx) => (
                      <span key={tagIdx} className="skill-tag">
                        {tag}
                        <button onClick={() => handleRemoveSkillTag(catIdx, tagIdx)}>×</button>
                      </span>
                    ))}
                  </div>

                  {/* Add Tag Input */}
                  <div className="tag-add-input-row">
                    <input
                      type="text"
                      className="tag-add-input"
                      placeholder="Add skill (press Enter or click Add)..."
                      value={newTagInput[catIdx] || ''}
                      onChange={(e) =>
                        setNewTagInput({ ...newTagInput, [catIdx]: e.target.value })
                      }
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddSkillTag(catIdx, newTagInput[catIdx]);
                        }
                      }}
                    />
                    <button
                      className="btn-resume btn-resume-outline"
                      style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem' }}
                      onClick={() => handleAddSkillTag(catIdx, newTagInput[catIdx])}
                    >
                      Add
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Section 4: Education */}
          {activeEditorTab === 'education' && (
            <div className="resume-section-body">
              <div className="resume-section-header">
                <div>
                  <h3 className="resume-section-title">Education</h3>
                  <p className="resume-section-desc">
                    Degrees, universities, relevant coursework, and academic honors. List in reverse chronological order.
                  </p>
                </div>
                <button className="btn-resume btn-resume-outline" onClick={handleAddEducation}>
                  <Plus size={14} /> Add Education
                </button>
              </div>

              {(currentResume.education || []).map((edu, eduIdx) => (
                <div key={eduIdx} className="dynamic-item-card">
                  <div className="dynamic-item-topbar">
                    <span className="dynamic-item-badge">Education #{eduIdx + 1}</span>
                    <button
                      className="btn-icon-control danger"
                      onClick={() => handleRemoveEducation(eduIdx)}
                      title="Delete education entry"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  <div className="form-grid-2">
                    <div className="form-group">
                      <label className="form-label">Institution / University *</label>
                      <input
                        type="text"
                        className="form-input"
                        value={edu.institution || ''}
                        onChange={(e) => handleEducationChange(eduIdx, 'institution', e.target.value)}
                        placeholder="e.g. Stanford University"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Degree *</label>
                      <input
                        type="text"
                        className="form-input"
                        value={edu.degree || ''}
                        onChange={(e) => handleEducationChange(eduIdx, 'degree', e.target.value)}
                        placeholder="e.g. Bachelor of Science"
                      />
                    </div>
                  </div>

                  <div className="form-grid-2">
                    <div className="form-group">
                      <label className="form-label">Field of Study</label>
                      <input
                        type="text"
                        className="form-input"
                        value={edu.field_of_study || ''}
                        onChange={(e) => handleEducationChange(eduIdx, 'field_of_study', e.target.value)}
                        placeholder="e.g. Computer Science"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">CGPA / Percentage (Optional)</label>
                      <input
                        type="text"
                        className="form-input"
                        value={edu.gpa || ''}
                        onChange={(e) => handleEducationChange(eduIdx, 'gpa', e.target.value)}
                        placeholder="e.g. 3.8 / 4.0 or 8.9 CGPA"
                      />
                    </div>
                  </div>

                  <div className="form-grid-2">
                    <div className="form-group">
                      <label className="form-label">Start Year / Date</label>
                      <input
                        type="text"
                        className="form-input"
                        value={edu.start_date || ''}
                        onChange={(e) => handleEducationChange(eduIdx, 'start_date', e.target.value)}
                        placeholder="e.g. Aug 2022"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Graduation Year / Date</label>
                      <input
                        type="text"
                        className="form-input"
                        value={edu.graduation_date || ''}
                        onChange={(e) => handleEducationChange(eduIdx, 'graduation_date', e.target.value)}
                        placeholder="e.g. May 2026 (Expected)"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Relevant Coursework</label>
                    <input
                      type="text"
                      className="form-input"
                      value={edu.coursework || ''}
                      onChange={(e) => handleEducationChange(eduIdx, 'coursework', e.target.value)}
                      placeholder="e.g. Data Structures & Algorithms, Database Systems, Web Development"
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Section 5: Projects */}
          {activeEditorTab === 'projects' && (
            <div className="resume-section-body">
              <div className="resume-section-header">
                <div>
                  <h3 className="resume-section-title">Projects</h3>
                  <p className="resume-section-desc">
                    Showcase real engineering projects you built. Highlight verified technologies and concrete outcomes.
                  </p>
                </div>
                <button className="btn-resume btn-resume-outline" onClick={handleAddProject}>
                  <Plus size={14} /> Add Project
                </button>
              </div>

              {/* Bullet Writing Guidance Box */}
              <div className="bullet-guidance-box">
                <span className="bullet-formula-tag">High-Impact Bullet Formula:</span>
                <span>
                  <strong>[Action Verb]</strong> + <strong>[Work Performed]</strong> + <strong>[Technology / Method]</strong> + <strong>[Actual Outcome]</strong>.
                  <br />
                  <em>Example:</em> "Architected a responsive task tracker using React and Vite, reducing mock interview setup time by 40%."
                </span>
              </div>

              {(currentResume.projects || []).map((proj, pIdx) => (
                <div key={pIdx} className="dynamic-item-card">
                  <div className="dynamic-item-topbar">
                    <span className="dynamic-item-badge">Project #{pIdx + 1}</span>
                    <button
                      className="btn-icon-control danger"
                      onClick={() => handleRemoveProject(pIdx)}
                      title="Delete project"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  <div className="form-grid-2">
                    <div className="form-group">
                      <label className="form-label">Project Title *</label>
                      <input
                        type="text"
                        className="form-input"
                        value={proj.title || ''}
                        onChange={(e) => handleProjectChange(pIdx, 'title', e.target.value)}
                        placeholder="e.g. SkillBridge Career Preparation Platform"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Dates / Timeline</label>
                      <input
                        type="text"
                        className="form-input"
                        value={proj.end_date || ''}
                        onChange={(e) => handleProjectChange(pIdx, 'end_date', e.target.value)}
                        placeholder="e.g. Jan 2024 – Mar 2024"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Technologies Used (comma separated)</label>
                    <input
                      type="text"
                      className="form-input"
                      value={(proj.technologies || []).join(', ')}
                      onChange={(e) => {
                        const tags = e.target.value
                          .split(',')
                          .map((t) => t.trim())
                          .filter(Boolean);
                        handleProjectChange(pIdx, 'technologies', tags);
                      }}
                      placeholder="e.g. React 19, FastAPI, SQLite, Pydantic"
                    />
                  </div>

                  <div className="form-grid-2">
                    <div className="form-group">
                      <label className="form-label">GitHub Repository URL</label>
                      <input
                        type="url"
                        className="form-input"
                        value={proj.github_url || ''}
                        onChange={(e) => handleProjectChange(pIdx, 'github_url', e.target.value)}
                        placeholder="https://github.com/username/project"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Live Demo URL</label>
                      <input
                        type="url"
                        className="form-input"
                        value={proj.live_url || ''}
                        onChange={(e) => handleProjectChange(pIdx, 'live_url', e.target.value)}
                        placeholder="https://demo-app.com"
                      />
                    </div>
                  </div>

                  {/* Bullet points editor */}
                  <div className="bullets-editor-container">
                    <label className="form-label">Contribution & Achievement Bullets</label>
                    {(proj.bullets || []).map((bullet, bIdx) => (
                      <div key={bIdx} className="bullet-item-row">
                        <textarea
                          className="form-input"
                          value={bullet}
                          onChange={(e) =>
                            handleProjectBulletChange(pIdx, bIdx, e.target.value)
                          }
                          placeholder="e.g. Developed RESTful endpoints using FastAPI, validating requests with Pydantic schemas..."
                        />
                        <button
                          className="btn-icon-control danger"
                          onClick={() => handleRemoveProjectBullet(pIdx, bIdx)}
                          title="Remove bullet"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                    <button
                      className="btn-add-bullet"
                      onClick={() => handleAddProjectBullet(pIdx)}
                    >
                      <Plus size={14} /> Add Bullet Point
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Section 6: Experience & Internships */}
          {activeEditorTab === 'experience' && (
            <div className="resume-section-body">
              <div className="resume-section-header">
                <div>
                  <h3 className="resume-section-title">Experience & Internships</h3>
                  <p className="resume-section-desc">
                    Formal internships, student work, or freelancing. If you have no formal work experience, this section can remain empty without penalty.
                  </p>
                </div>
                <button className="btn-resume btn-resume-outline" onClick={handleAddExperience}>
                  <Plus size={14} /> Add Experience
                </button>
              </div>

              {(currentResume.experience || []).length === 0 && (
                <div style={{ textAlign: 'center', padding: '2rem', background: 'var(--bg-subtle)', borderRadius: '8px', color: 'var(--text-muted)' }}>
                  <Briefcase size={28} style={{ margin: '0 auto 0.5rem auto', opacity: 0.5 }} />
                  <p style={{ fontWeight: 600 }}>No formal work experience added.</p>
                  <p style={{ fontSize: '0.825rem' }}>
                    Students are not expected to fabricate job titles. Keep this section empty or add an internship if you completed one.
                  </p>
                </div>
              )}

              {(currentResume.experience || []).map((exp, eIdx) => (
                <div key={eIdx} className="dynamic-item-card">
                  <div className="dynamic-item-topbar">
                    <span className="dynamic-item-badge">Experience #{eIdx + 1}</span>
                    <button
                      className="btn-icon-control danger"
                      onClick={() => handleRemoveExperience(eIdx)}
                      title="Delete experience entry"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  <div className="form-grid-2">
                    <div className="form-group">
                      <label className="form-label">Company / Organization *</label>
                      <input
                        type="text"
                        className="form-input"
                        value={exp.organization || ''}
                        onChange={(e) => handleExperienceChange(eIdx, 'organization', e.target.value)}
                        placeholder="e.g. TechCorp Solutions"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Job Title *</label>
                      <input
                        type="text"
                        className="form-input"
                        value={exp.job_title || ''}
                        onChange={(e) => handleExperienceChange(eIdx, 'job_title', e.target.value)}
                        placeholder="e.g. Software Engineering Intern"
                      />
                    </div>
                  </div>

                  <div className="form-grid-2">
                    <div className="form-group">
                      <label className="form-label">Dates / Duration</label>
                      <input
                        type="text"
                        className="form-input"
                        value={`${exp.start_date || ''} – ${exp.end_date || ''}`}
                        onChange={(e) => {
                          const parts = e.target.value.split('–');
                          handleExperienceChange(eIdx, 'start_date', parts[0]?.trim() || '');
                          if (parts[1]) {
                            handleExperienceChange(eIdx, 'end_date', parts[1]?.trim() || '');
                          }
                        }}
                        placeholder="e.g. May 2024 – Jul 2024"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Location</label>
                      <input
                        type="text"
                        className="form-input"
                        value={exp.location || ''}
                        onChange={(e) => handleExperienceChange(eIdx, 'location', e.target.value)}
                        placeholder="e.g. Remote / New York, NY"
                      />
                    </div>
                  </div>

                  {/* Bullet points editor */}
                  <div className="bullets-editor-container">
                    <label className="form-label">Responsibilities & Achievements</label>
                    {(exp.bullets || []).map((bullet, bIdx) => (
                      <div key={bIdx} className="bullet-item-row">
                        <textarea
                          className="form-input"
                          value={bullet}
                          onChange={(e) =>
                            handleExperienceBulletChange(eIdx, bIdx, e.target.value)
                          }
                          placeholder="e.g. Collaborated with a team of 4 engineers to build client-facing dashboard components..."
                        />
                        <button
                          className="btn-icon-control danger"
                          onClick={() => handleRemoveExperienceBullet(eIdx, bIdx)}
                          title="Remove bullet"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                    <button
                      className="btn-add-bullet"
                      onClick={() => handleAddExperienceBullet(eIdx)}
                    >
                      <Plus size={14} /> Add Bullet Point
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Section 7: Additional Sections Toggle */}
          {activeEditorTab === 'additional' && (
            <div className="resume-section-body">
              <div className="resume-section-header">
                <div>
                  <h3 className="resume-section-title">Optional Sections</h3>
                  <p className="resume-section-desc">
                    Enable or disable additional sections based on your background.
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', padding: '0.75rem', background: 'var(--bg-subtle)', borderRadius: '8px' }}>
                  <input
                    type="checkbox"
                    checked={currentResume.section_config?.enabled?.certifications || false}
                    onChange={() => handleToggleSection('certifications')}
                  />
                  <div>
                    <strong style={{ fontSize: '0.9rem' }}>Certifications & Training</strong>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Show AWS, Google Cloud, Oracle, or verified technical course certifications.</p>
                  </div>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', padding: '0.75rem', background: 'var(--bg-subtle)', borderRadius: '8px' }}>
                  <input
                    type="checkbox"
                    checked={currentResume.section_config?.enabled?.achievements || false}
                    onChange={() => handleToggleSection('achievements')}
                  />
                  <div>
                    <strong style={{ fontSize: '0.9rem' }}>Achievements & Awards</strong>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Hackathons, coding competition rankings, or academic scholarships.</p>
                  </div>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', padding: '0.75rem', background: 'var(--bg-subtle)', borderRadius: '8px' }}>
                  <input
                    type="checkbox"
                    checked={currentResume.section_config?.enabled?.leadership || false}
                    onChange={() => handleToggleSection('leadership')}
                  />
                  <div>
                    <strong style={{ fontSize: '0.9rem' }}>Leadership & Extracurricular Activities</strong>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Club presidency, student representative, or open-source community contributions.</p>
                  </div>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', padding: '0.75rem', background: 'var(--bg-subtle)', borderRadius: '8px' }}>
                  <input
                    type="checkbox"
                    checked={currentResume.section_config?.enabled?.languages || false}
                    onChange={() => handleToggleSection('languages')}
                  />
                  <div>
                    <strong style={{ fontSize: '0.9rem' }}>Languages</strong>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Spoken languages and proficiencies.</p>
                  </div>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* ====================================================================
            RIGHT PANE: Live ATS Preview, Quality Review & Job Tailoring
            ==================================================================== */}
        <div className={`resume-preview-pane ${mobileView === 'editor' ? 'hide-mobile' : ''}`}>
          {/* Sub Tab Navigation */}
          <div className="preview-nav-tabs">
            <button
              className={`preview-nav-btn ${activePreviewTab === 'preview' ? 'active' : ''}`}
              onClick={() => setActivePreviewTab('preview')}
            >
              <FileText size={16} /> Live ATS Preview
            </button>
            <button
              className={`preview-nav-btn ${activePreviewTab === 'review' ? 'active' : ''}`}
              onClick={() => {
                setActivePreviewTab('review');
                if (currentResume.id) triggerReview(currentResume.id);
              }}
            >
              <Sparkles size={16} />
              ATS Review
              {reviewData?.critical_issues?.length > 0 && (
                <span style={{ background: '#dc2626', color: '#fff', fontSize: '0.7rem', padding: '0.1rem 0.4rem', borderRadius: '10px' }}>
                  {reviewData.critical_issues.length}
                </span>
              )}
            </button>
            <button
              className={`preview-nav-btn ${activePreviewTab === 'tailor' ? 'active' : ''}`}
              onClick={() => {
                setActivePreviewTab('tailor');
                if (currentResume.id && currentResume.target_job_id) {
                  triggerTailor(currentResume.id, currentResume.target_job_id);
                }
              }}
            >
              <Briefcase size={16} /> Job Tailoring
            </button>
          </div>

          {/* TAB 1: LIVE ATS DOCUMENT PREVIEW */}
          {activePreviewTab === 'preview' && (
            <div className="resume-sheet-container">
              <div id="resume-printable-document" className="resume-ats-sheet">
                {/* 1. Contact Header */}
                <div className="ats-name-header">
                  <h1>{contactInfo.full_name || 'Your Full Name'}</h1>
                </div>

                <div className="ats-contact-bar">
                  {contactInfo.email && <span className="ats-contact-item">{contactInfo.email}</span>}
                  {contactInfo.phone && (
                    <>
                      <span className="ats-contact-sep">|</span>
                      <span className="ats-contact-item">{contactInfo.phone}</span>
                    </>
                  )}
                  {contactInfo.location && (
                    <>
                      <span className="ats-contact-sep">|</span>
                      <span className="ats-contact-item">{contactInfo.location}</span>
                    </>
                  )}
                  {contactInfo.linkedin_url && (
                    <>
                      <span className="ats-contact-sep">|</span>
                      <span className="ats-contact-item">{contactInfo.linkedin_url.replace(/^https?:\/\/(www\.)?/, '')}</span>
                    </>
                  )}
                  {contactInfo.github_url && (
                    <>
                      <span className="ats-contact-sep">|</span>
                      <span className="ats-contact-item">{contactInfo.github_url.replace(/^https?:\/\/(www\.)?/, '')}</span>
                    </>
                  )}
                  {contactInfo.portfolio_url && (
                    <>
                      <span className="ats-contact-sep">|</span>
                      <span className="ats-contact-item">{contactInfo.portfolio_url.replace(/^https?:\/\/(www\.)?/, '')}</span>
                    </>
                  )}
                </div>

                {/* 2. Professional Summary */}
                {currentResume.summary && currentResume.section_config?.enabled?.summary !== false && (
                  <div className="ats-section">
                    <div className="ats-section-heading">Professional Summary</div>
                    <p className="ats-summary-text">{currentResume.summary}</p>
                  </div>
                )}

                {/* 3. Technical Skills */}
                {currentResume.skills && currentResume.skills.length > 0 && currentResume.section_config?.enabled?.skills !== false && (
                  <div className="ats-section">
                    <div className="ats-section-heading">Technical Skills</div>
                    {currentResume.skills.map((cat, idx) => (
                      <div key={idx} className="ats-skill-line">
                        <span className="ats-skill-cat">{cat.category}: </span>
                        <span>{(cat.items || []).join(', ')}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* 4. Education */}
                {currentResume.education && currentResume.education.length > 0 && currentResume.section_config?.enabled?.education !== false && (
                  <div className="ats-section">
                    <div className="ats-section-heading">Education</div>
                    {currentResume.education.map((edu, idx) => (
                      <div key={idx} className="ats-entry">
                        <div className="ats-entry-header">
                          <div>
                            <span className="ats-entry-title">{edu.institution}</span>
                            {edu.degree && (
                              <span className="ats-entry-subtitle"> — {edu.degree}{edu.field_of_study ? ` in ${edu.field_of_study}` : ''}</span>
                            )}
                          </div>
                          {(edu.start_date || edu.graduation_date) && (
                            <div className="ats-entry-date">
                              {edu.start_date ? `${edu.start_date} – ` : ''}{edu.graduation_date || ''}
                            </div>
                          )}
                        </div>
                        {edu.gpa && (
                          <div style={{ fontSize: '9.5pt', color: '#475569' }}>
                            Cumulative Grade: {edu.gpa}
                          </div>
                        )}
                        {edu.coursework && (
                          <div style={{ fontSize: '9pt', color: '#475569', marginTop: '2px' }}>
                            <strong>Relevant Coursework:</strong> {edu.coursework}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* 5. Technical Projects */}
                {currentResume.projects && currentResume.projects.length > 0 && currentResume.section_config?.enabled?.projects !== false && (
                  <div className="ats-section">
                    <div className="ats-section-heading">Projects</div>
                    {currentResume.projects.map((proj, idx) => (
                      <div key={idx} className="ats-entry">
                        <div className="ats-entry-header">
                          <div>
                            <span className="ats-entry-title">{proj.title}</span>
                            {proj.github_url && (
                              <span style={{ fontSize: '9pt', color: '#475569', marginLeft: '8px' }}>
                                ({proj.github_url.replace(/^https?:\/\/(www\.)?/, '')})
                              </span>
                            )}
                          </div>
                          {proj.end_date && (
                            <div className="ats-entry-date">{proj.end_date}</div>
                          )}
                        </div>
                        {proj.technologies && proj.technologies.length > 0 && (
                          <div className="ats-entry-techs">
                            <strong>Technologies:</strong> {proj.technologies.join(', ')}
                          </div>
                        )}
                        {proj.bullets && proj.bullets.length > 0 && (
                          <ul className="ats-bullets-list">
                            {proj.bullets.map((b, bIdx) => (
                              b.trim() && <li key={bIdx} className="ats-bullet-point">{b}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* 6. Experience & Internships */}
                {currentResume.experience && currentResume.experience.length > 0 && currentResume.section_config?.enabled?.experience !== false && (
                  <div className="ats-section">
                    <div className="ats-section-heading">Experience & Internships</div>
                    {currentResume.experience.map((exp, idx) => (
                      <div key={idx} className="ats-entry">
                        <div className="ats-entry-header">
                          <div>
                            <span className="ats-entry-title">{exp.job_title}</span>
                            <span className="ats-entry-subtitle"> — {exp.organization}</span>
                          </div>
                          {(exp.start_date || exp.end_date) && (
                            <div className="ats-entry-date">
                              {exp.start_date ? `${exp.start_date} – ` : ''}{exp.end_date || ''}
                            </div>
                          )}
                        </div>
                        {exp.bullets && exp.bullets.length > 0 && (
                          <ul className="ats-bullets-list">
                            {exp.bullets.map((b, bIdx) => (
                              b.trim() && <li key={bIdx} className="ats-bullet-point">{b}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* 7. Certifications */}
                {currentResume.section_config?.enabled?.certifications && (
                  <div className="ats-section">
                    <div className="ats-section-heading">Certifications</div>
                    <ul className="ats-bullets-list">
                      <li className="ats-bullet-point">AWS Certified Cloud Practitioner — Amazon Web Services (2024)</li>
                      <li className="ats-bullet-point">Meta Front-End Developer Professional Certificate — Coursera (2023)</li>
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: ATS QUALITY REVIEW */}
          {activePreviewTab === 'review' && (
            <div className="resume-review-pane">
              {isReviewLoading ? (
                <div style={{ textAlign: 'center', padding: '3rem' }}>
                  <RefreshCw size={28} className="spin" style={{ margin: '0 auto 0.75rem auto', color: 'var(--primary)' }} />
                  <p>Analyzing resume against ATS best practices...</p>
                </div>
              ) : reviewData ? (
                <>
                  {/* Overall Quality Score */}
                  <div className="review-score-hero">
                    <div className="review-score-circle">
                      <span className="score-num">{reviewData.overall_score}</span>
                      <span className="score-total">/ 100</span>
                    </div>
                    <div className="review-score-summary">
                      <h4 className="review-score-title">ATS Format & Content Readiness</h4>
                      <p className="review-score-desc">{reviewData.summary_critique}</p>
                    </div>
                  </div>

                  {/* Score Breakdown Bars */}
                  <div className="review-breakdown-grid">
                    {Object.entries(reviewData.score_breakdown || {}).map(([key, val]) => (
                      <div key={key} className="breakdown-bar-item">
                        <div className="breakdown-label-row">
                          <span style={{ textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</span>
                          <span>{val} pts</span>
                        </div>
                        <div className="breakdown-track">
                          <div
                            className="breakdown-fill"
                            style={{
                              width: `${Math.min(100, (val / 25) * 100)}%`,
                              background: val > 15 ? 'var(--success)' : val > 8 ? 'var(--warning)' : '#dc2626'
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Critical Issues */}
                  {reviewData.critical_issues?.length > 0 && (
                    <div className="review-issues-section">
                      <h5 className="review-issues-title" style={{ color: '#dc2626' }}>
                        <AlertCircle size={16} /> Critical Issues ({reviewData.critical_issues.length})
                      </h5>
                      {reviewData.critical_issues.map((iss, i) => (
                        <div key={i} className="issue-card critical">
                          <div className="issue-top">{iss.title}</div>
                          <div className="issue-detail">{iss.detail}</div>
                          <div className="issue-hint">💡 Action: {iss.action_hint}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Recommended Improvements */}
                  {reviewData.recommended_improvements?.length > 0 && (
                    <div className="review-issues-section">
                      <h5 className="review-issues-title" style={{ color: '#b45309' }}>
                        <AlertTriangle size={16} /> Recommended Improvements ({reviewData.recommended_improvements.length})
                      </h5>
                      {reviewData.recommended_improvements.map((imp, i) => (
                        <div key={i} className="issue-card improvement">
                          <div className="issue-top">{imp.title}</div>
                          <div className="issue-detail">{imp.detail}</div>
                          <div className="issue-hint">💡 Suggestion: {imp.action_hint}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Bullet Phrasing Insights */}
                  {reviewData.bullet_insights?.length > 0 && (
                    <div className="review-issues-section">
                      <h5 className="review-issues-title">
                        <CheckCircle2 size={16} style={{ color: 'var(--primary)' }} /> Bullet Phrasing Insights
                      </h5>
                      <div className="bullet-insights-list">
                        {reviewData.bullet_insights.slice(0, 5).map((insight, idx) => (
                          <div key={idx} className="bullet-insight-card">
                            <div className="bullet-insight-meta">
                              <span>{insight.section}: {insight.item_title}</span>
                              {insight.has_action_verb ? (
                                <span style={{ color: 'var(--success)' }}>✓ Strong Verb: "{insight.detected_action_verb}"</span>
                              ) : (
                                <span style={{ color: 'var(--warning)' }}>Weak Action Verb</span>
                              )}
                            </div>
                            <div className="bullet-snippet">"{insight.bullet_text}"</div>
                            {insight.improvement_suggestion && (
                              <div className="bullet-suggestion">
                                💡 {insight.improvement_suggestion}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  Save or refresh draft to run ATS quality review.
                </div>
              )}
            </div>
          )}

          {/* TAB 3: JOB TAILORING & KEYWORD MATCHING */}
          {activePreviewTab === 'tailor' && (
            <div className="resume-tailor-pane">
              {!currentResume.target_job_id ? (
                <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                  <Briefcase size={32} style={{ margin: '0 auto 0.75rem auto', opacity: 0.5 }} />
                  <h4 style={{ color: 'var(--text-main)', marginBottom: '0.5rem' }}>No Target Job Selected</h4>
                  <p style={{ fontSize: '0.875rem', maxWidth: '420px', margin: '0 auto' }}>
                    Select a tracked opportunity from the <strong>Tailor Job</strong> dropdown at the top to compare required keywords against your resume.
                  </p>
                </div>
              ) : isTailorLoading ? (
                <div style={{ textAlign: 'center', padding: '3rem' }}>
                  <RefreshCw size={28} className="spin" style={{ margin: '0 auto 0.75rem auto', color: 'var(--primary)' }} />
                  <p>Comparing resume keywords with target job description...</p>
                </div>
              ) : tailorData ? (
                <>
                  {/* Job Header Banner */}
                  <div className="tailor-job-banner">
                    <div className="tailor-job-info">
                      <h3>{tailorData.target_job_company}</h3>
                      <p>{tailorData.target_job_title}</p>
                    </div>
                    <div className="tailor-match-badge">
                      <div className="match-pct">{tailorData.keyword_match_percentage}%</div>
                      <div className="match-lbl">Keyword Alignment</div>
                    </div>
                  </div>

                  <div className="keyword-grid">
                    {/* 1. Present Keywords */}
                    <div>
                      <h4 className="keyword-group-title" style={{ color: '#15803d' }}>
                        ✓ Relevant Keywords Present in Resume ({tailorData.present_keywords?.length || 0})
                      </h4>
                      <div className="keyword-tags">
                        {(tailorData.present_keywords || []).map((kw, i) => (
                          <span key={i} className="kw-pill present">
                            {kw.keyword}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* 2. Missing Required Keywords */}
                    <div>
                      <h4 className="keyword-group-title" style={{ color: '#b91c1c' }}>
                        ⚠️ Missing Required Keywords ({tailorData.missing_required_keywords?.length || 0})
                      </h4>
                      <div className="keyword-tags">
                        {(tailorData.missing_required_keywords || []).map((kw, i) => (
                          <span key={i} className="kw-pill missing-req">
                            {kw.keyword}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* 3. Missing Preferred Keywords */}
                    <div>
                      <h4 className="keyword-group-title" style={{ color: '#b45309' }}>
                        ℹ️ Missing Preferred Keywords ({tailorData.missing_preferred_keywords?.length || 0})
                      </h4>
                      <div className="keyword-tags">
                        {(tailorData.missing_preferred_keywords || []).map((kw, i) => (
                          <span key={i} className="kw-pill missing-pref">
                            {kw.keyword}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* 4. Actionable Alignment Suggestions */}
                    <div>
                      <h4 className="keyword-group-title">
                        💡 Truthful Tailoring Recommendations
                      </h4>
                      <div className="alignment-suggestions-list">
                        {(tailorData.truthful_alignment_suggestions || []).map((sug, i) => (
                          <div key={i} className="alignment-card">
                            {sug}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && (
        <div className="resume-modal-overlay">
          <div className="resume-modal-card">
            <h3 className="resume-modal-title">Delete Resume Draft</h3>
            <p className="resume-modal-body">
              Are you sure you want to delete <strong>"{currentResume.title}"</strong>? This action cannot be undone. Associated job applications will not be affected.
            </p>
            <div className="resume-modal-actions">
              <button
                className="btn-resume btn-resume-outline"
                onClick={() => setDeleteModalOpen(false)}
              >
                Cancel
              </button>
              <button
                className="btn-resume btn-resume-danger"
                onClick={handleDeleteDraft}
              >
                Delete Resume
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sample Resume Confirmation Modal */}
      {sampleModalOpen && (
        <div className="resume-modal-overlay">
          <div className="resume-modal-card">
            <h3 className="resume-modal-title">Load Sample Resume</h3>
            <p className="resume-modal-body">
              This will create a new draft labeled <strong>"Sample: Frontend Developer Resume"</strong> with verified, realistic entry-level content. Your current draft will <strong>not</strong> be overwritten.
            </p>
            <div className="resume-modal-actions">
              <button
                className="btn-resume btn-resume-outline"
                onClick={() => setSampleModalOpen(false)}
              >
                Cancel
              </button>
              <button
                className="btn-resume btn-resume-primary"
                onClick={handleLoadSampleResume}
              >
                Load Sample Draft
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
