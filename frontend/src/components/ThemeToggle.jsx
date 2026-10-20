import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function ThemeToggle({ showLabel = true, className = '' }) {
  const { theme, isDark, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      className={`theme-toggle-btn ${isDark ? 'is-dark' : 'is-light'} ${className}`}
      onClick={toggleTheme}
      title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
      aria-label={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
    >
      <div className="theme-toggle-track">
        <span className={`theme-toggle-thumb ${isDark ? 'thumb-dark' : 'thumb-light'}`}>
          {isDark ? (
            <Moon size={14} className="theme-icon moon-icon" />
          ) : (
            <Sun size={14} className="theme-icon sun-icon" />
          )}
        </span>
      </div>
      {showLabel && (
        <span className="theme-toggle-label">
          {isDark ? 'Dark' : 'Light'}
        </span>
      )}
    </button>
  );
}
