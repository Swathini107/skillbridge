/**
 * SkillBridge API Service Client
 * Handles communication with the FastAPI backend for health and application tracking.
 */

const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

async function request(endpoint, options = {}) {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorDetail = `HTTP error ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          if (Array.isArray(errorJson.detail)) {
            errorDetail = errorJson.detail.map((d) => d.msg || `${d.loc?.join('.')}: error`).join(', ');
          } else {
            errorDetail = errorJson.detail;
          }
        }
      } catch {
        // use fallback status
      }
      throw new Error(errorDetail);
    }

    // Check if response has content
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      return { ok: true, data };
    }
    return { ok: true, data: null };
  } catch (err) {
    return { ok: false, error: err.message || 'Network request failed' };
  }
}

// 1. Health check
export async function fetchHealth() {
  return request('/api/health');
}

// 2. Applications List with Search, Filter & Sort
export async function getApplications(params = {}) {
  const query = new URLSearchParams();
  if (params.search) query.append('search', params.search);
  if (params.status && params.status !== 'All') query.append('status', params.status);
  if (params.work_mode && params.work_mode !== 'All') query.append('work_mode', params.work_mode);
  if (params.employment_type && params.employment_type !== 'All') query.append('employment_type', params.employment_type);
  if (params.sort_by) query.append('sort_by', params.sort_by);
  if (params.sort_order) query.append('sort_order', params.sort_order);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return request(`/api/applications${queryString}`);
}

// 3. Application Summary Stats
export async function getApplicationStats() {
  return request('/api/applications/stats');
}

// 4. Get Single Application
export async function getApplicationById(id) {
  return request(`/api/applications/${id}`);
}

// 5. Create Application
export async function createApplication(data) {
  return request('/api/applications', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// 6. Update Application
export async function updateApplication(id, data) {
  return request(`/api/applications/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// 7. Update Application Status
export async function updateApplicationStatus(id, application_status) {
  return request(`/api/applications/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ application_status }),
  });
}

// 8. Delete Application
export async function deleteApplication(id) {
  return request(`/api/applications/${id}`, {
    method: 'DELETE',
  });
}

// 9. Analyze Job Description & Profile
export async function analyzeJob(payload) {
  return request('/api/analyzer/analyze', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// 10. Get Analysis History
export async function getAnalysisHistory() {
  return request('/api/analyzer/history');
}

// 11. Get Single Analysis Details
export async function getAnalysisById(id) {
  return request(`/api/analyzer/history/${id}`);
}

// 12. Delete Analysis History
export async function deleteAnalysis(id) {
  return request(`/api/analyzer/history/${id}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// 13. INTERVIEW MEMORY BANK (DAY 4)
// ============================================================================

export async function getQuestions(params = {}) {
  const query = new URLSearchParams();
  if (params.search) query.append('search', params.search);
  if (params.round_type && params.round_type !== 'All') query.append('round_type', params.round_type);
  if (params.difficulty && params.difficulty !== 'All') query.append('difficulty', params.difficulty);
  if (params.review_status && params.review_status !== 'All') query.append('review_status', params.review_status);
  if (params.company_name && params.company_name !== 'All') query.append('company_name', params.company_name);
  if (params.job_role) query.append('job_role', params.job_role);
  if (params.topic && params.topic !== 'All') query.append('topic', params.topic);
  if (params.job_id) query.append('job_id', params.job_id);
  if (params.sort_by) query.append('sort_by', params.sort_by);
  if (params.order) query.append('order', params.order);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return request(`/api/questions${queryString}`);
}

export async function getQuestionStats() {
  return request('/api/questions/stats');
}

export async function getQuestionById(id) {
  return request(`/api/questions/${id}`);
}

export async function createQuestion(data) {
  return request('/api/questions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateQuestion(id, data) {
  return request(`/api/questions/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function updateQuestionStatus(id, review_status) {
  return request(`/api/questions/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ review_status }),
  });
}

export async function deleteQuestion(id) {
  return request(`/api/questions/${id}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// 14. MOCK INTERVIEW PRACTICE STUDIO (DAY 5)
// ============================================================================

export async function previewPracticeSession(payload) {
  return request('/api/practice/preview', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function startPracticeSession(payload) {
  return request('/api/practice/sessions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getPracticeSessions(params = {}) {
  const query = new URLSearchParams();
  if (params.status && params.status !== 'All') query.append('status', params.status);
  if (params.round_type && params.round_type !== 'All') query.append('round_type', params.round_type);
  if (params.search) query.append('search', params.search);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return request(`/api/practice/sessions${queryString}`);
}

export async function getPracticeSessionById(id) {
  return request(`/api/practice/sessions/${id}`);
}

export async function updatePracticeAnswer(sessionId, answerId, payload, queryParams = {}) {
  const query = new URLSearchParams();
  if (queryParams.current_index !== undefined && queryParams.current_index !== null) {
    query.append('current_index', queryParams.current_index);
  }
  if (queryParams.duration_seconds !== undefined && queryParams.duration_seconds !== null) {
    query.append('duration_seconds', queryParams.duration_seconds);
  }

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return request(`/api/practice/sessions/${sessionId}/answers/${answerId}${queryString}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function finishPracticeSession(sessionId, payload = {}) {
  return request(`/api/practice/sessions/${sessionId}/finish`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function resumePracticeSession(sessionId) {
  return request(`/api/practice/sessions/${sessionId}/resume`, {
    method: 'POST',
  });
}

export async function getPracticeSessionReport(sessionId) {
  return request(`/api/practice/sessions/${sessionId}/report`);
}

export async function deletePracticeSession(sessionId) {
  return request(`/api/practice/sessions/${sessionId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// 15. UNIFIED DASHBOARD (DAYS 6 & 7)
// ============================================================================

export async function getDashboardSummary() {
  return request('/api/dashboard/summary');
}

// ============================================================================
// 16. ATS-FRIENDLY RESUME BUILDER
// ============================================================================

export async function getResumes() {
  return request('/api/resumes');
}

export async function getResumeById(id) {
  return request(`/api/resumes/${id}`);
}

export async function getSampleResume(role = 'frontend') {
  return request(`/api/resumes/sample?role=${encodeURIComponent(role)}`);
}

export async function createResume(data) {
  return request('/api/resumes', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateResume(id, data) {
  return request(`/api/resumes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function duplicateResume(id) {
  return request(`/api/resumes/${id}/duplicate`, {
    method: 'POST',
  });
}

export async function deleteResume(id) {
  return request(`/api/resumes/${id}`, {
    method: 'DELETE',
  });
}

export async function reviewResume(id) {
  return request(`/api/resumes/${id}/review`, {
    method: 'POST',
  });
}

export async function tailorResume(id, jobId) {
  return request(`/api/resumes/${id}/tailor/${jobId}`, {
    method: 'POST',
  });
}

export function getDocxExportUrl(id) {
  return `${API_BASE_URL}/api/resumes/${id}/export/docx`;
}
