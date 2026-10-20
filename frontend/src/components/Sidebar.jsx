import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileSearch,
  Briefcase,
  HelpCircle,
  Mic,
  Sparkles,
  FileText,
  X
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';

const navItems = [
  {
    name: 'Dashboard',
    path: '/',
    icon: LayoutDashboard
  },
  {
    name: 'Resume Builder',
    path: '/resume-builder',
    icon: FileText
  },
  {
    name: 'Job Analyzer',
    path: '/job-analyzer',
    icon: FileSearch
  },
  {
    name: 'My Applications',
    path: '/applications',
    icon: Briefcase
  },
  {
    name: 'Interview Questions',
    path: '/questions',
    icon: HelpCircle
  },
  {
    name: 'Mock Interview',
    path: '/practice',
    icon: Mic
  }
];

export default function Sidebar({ isOpen, onClose }) {
  return (
    <>
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="brand-icon">
            <Sparkles size={20} />
          </div>
          <div className="brand-text">
            <h1>SkillBridge</h1>
            <span>Career Preparation</span>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="menu-toggle"
              style={{ marginLeft: 'auto', color: '#94a3b8' }}
              aria-label="Close menu"
            >
              <X size={20} />
            </button>
          )}
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
                onClick={onClose}
                end={item.path === '/'}
              >
                <Icon size={18} />
                <span>{item.name}</span>
                {item.badge && <span className="nav-badge">{item.badge}</span>}
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="day-badge-card">
            <div className="day-badge-icon">
              <Sparkles size={16} />
            </div>
            <div className="day-badge-info">
              <h4>SkillBridge v1.0</h4>
              <p>Career Readiness Platform</p>
            </div>
          </div>
          <ThemeToggle className="sidebar-theme-toggle" />
        </div>
      </aside>
    </>
  );
}
