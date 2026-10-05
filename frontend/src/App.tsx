import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import { Profile } from './pages/Profile';
import { History } from './pages/History';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { Activity, User, History as HistoryIcon, BarChart2, Settings as SettingsIcon } from 'lucide-react';

function App() {
  const [view, setView] = useState<"dashboard" | "profile" | "history" | "analytics" | "settings">("dashboard");

  return (
    <div style={{ height: '100vh', display: 'flex', backgroundColor: 'var(--bg)', color: 'var(--text)' }}>
        {/* Sidebar */}
        <aside style={{ width: '240px', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--surface-1)' }}>
            <div style={{ padding: '24px', borderBottom: '1px solid var(--border)' }}>
                <h1 style={{ margin: 0, fontSize: '1.2rem', letterSpacing: '2px', fontWeight: 700 }}>VIGIL</h1>
                <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>DriveGuard AI</span>
            </div>
            <nav style={{ flex: 1, padding: '16px 0', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <NavItem icon={<Activity />} label="Live Monitor" active={view === "dashboard"} onClick={() => setView("dashboard")} />
                <NavItem icon={<User />} label="Driver Profile" active={view === "profile"} onClick={() => setView("profile")} />
                <NavItem icon={<HistoryIcon />} label="Session History" active={view === "history"} onClick={() => setView("history")} />
                <NavItem icon={<BarChart2 />} label="Analytics" active={view === "analytics"} onClick={() => setView("analytics")} />
                <NavItem icon={<SettingsIcon />} label="Settings" active={view === "settings"} onClick={() => setView("settings")} />
            </nav>
        </aside>

        {/* Main Content */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <header style={{ height: '64px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', padding: '0 24px', justifyContent: 'flex-end', backgroundColor: 'var(--surface-1)' }}>
                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                    <div style={{ padding: '4px 8px', backgroundColor: 'rgba(0, 255, 128, 0.2)', color: 'var(--safe)', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>LIVE</div>
                    <div className="mono">DR-001 Rahul</div>
                    <button style={{ background: 'transparent', border: '1px solid var(--border-strong)', color: 'var(--text)', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>End Session</button>
                </div>
            </header>
            <main style={{ flex: 1, overflow: 'auto', padding: '0' }}>
                {view === "dashboard" && <Dashboard />}
                {view === "profile" && <Profile />}
                {view === "history" && <History />}
                {view === "analytics" && <Analytics />}
                {view === "settings" && <Settings />}
            </main>
        </div>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }: any) {
    return (
        <button 
            onClick={onClick}
            style={{ 
                display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 24px', 
                background: active ? 'var(--surface-2)' : 'transparent',
                color: active ? 'var(--text)' : 'var(--text-dim)',
                border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer',
                borderLeft: active ? '3px solid var(--safe)' : '3px solid transparent'
            }}>
            {icon}
            <span style={{ fontWeight: active ? 600 : 400 }}>{label}</span>
        </button>
    );
}

export default App;
