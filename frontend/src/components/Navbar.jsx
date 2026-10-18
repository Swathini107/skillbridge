import React, { useEffect, useState, useCallback } from 'react';
import { Menu } from 'lucide-react';
import { fetchHealth } from '../services/api';

export default function Navbar({ onToggleMenu, currentTitle = 'Student Career Dashboard' }) {
  const [healthStatus, setHealthStatus] = useState({
    loading: true,
    connected: false,
    app: null
  });

  const checkStatus = useCallback(async () => {
    const res = await fetchHealth();
    if (res.ok && res.data.status === 'ok') {
      setHealthStatus({
        loading: false,
        connected: true,
        app: res.data.app || 'SkillBridge'
      });
    } else {
      setHealthStatus({
        loading: false,
        connected: false,
        app: null
      });
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    fetchHealth().then((res) => {
      if (!isMounted) return;
      if (res.ok && res.data.status === 'ok') {
        setHealthStatus({
          loading: false,
          connected: true,
          app: res.data.app || 'SkillBridge'
        });
      } else {
        setHealthStatus({
          loading: false,
          connected: false,
          app: null
        });
      }
    });

    const interval = setInterval(checkStatus, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [checkStatus]);

  return (
    <header className="top-navbar">
      <div className="navbar-left">
        <button
          className="menu-toggle"
          onClick={onToggleMenu}
          aria-label="Toggle navigation menu"
        >
          <Menu size={20} />
        </button>
        <div className="page-title-crumb">
          <span>{currentTitle}</span>
          <span className="crumb-tag">Day 1</span>
        </div>
      </div>

      <div className="navbar-right">
        {/* Live Backend Health Indicator */}
        <div
          className={`health-badge ${
            healthStatus.loading
              ? 'loading'
              : healthStatus.connected
              ? 'ok'
              : 'error'
          }`}
          title={
            healthStatus.connected
              ? `FastAPI health endpoint verified (/api/health)`
              : `FastAPI backend not detected at /api/health`
          }
        >
          <span className="pulse-dot"></span>
          <span className="label">
            {healthStatus.loading
              ? 'Checking backend...'
              : healthStatus.connected
              ? `Backend: OK (${healthStatus.app})`
              : 'Backend: Offline'}
          </span>
        </div>

        {/* Demo User Pill */}
        <div className="user-pill">
          <div className="user-avatar">S</div>
          <span>Student Demo</span>
        </div>
      </div>
    </header>
  );
}
