import React, { useState, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import './styles/index.css';
import './styles/layout.css';
import './styles/dashboard.css';
import './styles/applications.css';
import './styles/analyzer.css';
import './styles/questions.css';
import './styles/practice.css';
import './styles/resume.css';

// Lazy-loaded route components for optimal bundle splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Applications = lazy(() => import('./pages/Applications'));
const JobAnalyzer = lazy(() => import('./pages/JobAnalyzer'));
const InterviewQuestions = lazy(() => import('./pages/InterviewQuestions'));
const MockInterview = lazy(() => import('./pages/MockInterview'));
const ResumeBuilder = lazy(() => import('./pages/ResumeBuilder'));
const PlaceholderPage = lazy(() => import('./pages/PlaceholderPage'));

const pageTitleMap = {
  '/': 'Student Career Dashboard',
  '/resume-builder': 'ATS-Friendly Resume Builder',
  '/job-analyzer': 'Job Description Analyzer',
  '/applications': 'Job Application Tracker',
  '/questions': 'Interview Memory Bank',
  '/interview-questions': 'Interview Memory Bank',
  '/practice': 'Mock Interview Practice Studio',
  '/mock-interview': 'Mock Interview Practice Studio',
  '/recommendations': 'Career Recommendations'
};

function RouteLoadingFallback() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '50vh',
      gap: '12px',
      color: 'var(--text-muted)'
    }}>
      <div style={{
        width: '32px',
        height: '32px',
        border: '3px solid var(--border-subtle)',
        borderTopColor: 'var(--primary)',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite'
      }} />
      <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>Loading module...</span>
    </div>
  );
}

function AppContent() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const currentTitle = pageTitleMap[location.pathname] || 'SkillBridge Workspace';

  return (
    <div className="app-layout">
      {/* Mobile backdrop overlay */}
      <div
        className={`mobile-overlay ${sidebarOpen ? 'active' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Navigation Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <Navbar
          currentTitle={currentTitle}
          onToggleMenu={() => setSidebarOpen(!sidebarOpen)}
        />

        <main className="content-container">
          <Suspense fallback={<RouteLoadingFallback />}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/resume-builder" element={<ResumeBuilder />} />
              <Route path="/job-analyzer" element={<JobAnalyzer />} />
              <Route path="/applications" element={<Applications />} />
              <Route path="/questions" element={<InterviewQuestions />} />
              <Route path="/interview-questions" element={<InterviewQuestions />} />
              <Route path="/practice" element={<MockInterview />} />
              <Route path="/mock-interview" element={<MockInterview />} />
              <Route path="/recommendations" element={<Navigate to="/" replace />} />
              <Route path="*" element={<PlaceholderPage />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </ThemeProvider>
  );
}
