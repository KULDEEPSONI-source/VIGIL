import { useState } from 'react';
import {
  Activity,
  User,
  History as HistoryIcon,
  BarChart3,
  Settings as SettingsIcon,
  Radio,
  LogOut,
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import { Profile } from './pages/Profile';
import { History } from './pages/History';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import './App.css';

type View = 'dashboard' | 'profile' | 'history' | 'analytics' | 'settings';

const navItems: Array<{ id: View; label: string; icon: typeof Activity }> = [
  { id: 'dashboard', label: 'Live Monitor', icon: Activity },
  { id: 'profile', label: 'Driver Profile', icon: User },
  { id: 'history', label: 'Session History', icon: HistoryIcon },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
];

function App() {
  const [view, setView] = useState<View>('dashboard');

  const pageTitle = navItems.find((item) => item.id === view)?.label ?? 'Live Monitor';

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">V</div>
          <div>
            <div className="brand-name">VIGIL</div>
            <div className="brand-subtitle">DriveGuard AI</div>
          </div>
        </div>

        <div className="sidebar-status">
          <span className="status-dot" />
          AI SYSTEM ONLINE
        </div>

        <nav className="sidebar-nav" aria-label="Primary navigation">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`nav-item ${view === id ? 'active' : ''}`}
              onClick={() => setView(id)}
            >
              <Icon size={19} strokeWidth={1.8} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-footer-card">
            <Radio size={16} />
            <div>
              <div className="footer-label">DETECTION</div>
              <div className="footer-value">Active</div>
            </div>
          </div>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-page">
            <span className="topbar-kicker">VIGIL /</span>
            <span>{pageTitle}</span>
          </div>

          <div className="topbar-actions">
            <div className="live-pill">
              <span className="status-dot" />
              LIVE
            </div>
            <div className="driver-chip">
              <span className="driver-id">DR-001</span>
              <span>Rahul</span>
            </div>
            <button className="end-session">
              <LogOut size={15} />
              End Session
            </button>
          </div>
        </header>

        <main className="page-content">
          {view === 'dashboard' && <Dashboard />}
          {view === 'profile' && <Profile />}
          {view === 'history' && <History />}
          {view === 'analytics' && <Analytics />}
          {view === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
}

export default App;
