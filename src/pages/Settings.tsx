import { useEffect, useState } from 'react';
import { Bell, BrainCircuit, Info, Volume2, SlidersHorizontal, Palette } from 'lucide-react';

export function Settings() {
  const [sensitivity, setSensitivity] = useState(50);
  const [sound, setSound] = useState(true);
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    const saved = localStorage.getItem('vigil_settings');
    if (saved) {
      try {
        const s = JSON.parse(saved);
        if (s.sensitivity !== undefined) setSensitivity(s.sensitivity);
        if (s.sound !== undefined) setSound(s.sound);
        if (s.theme) setTheme(s.theme);
      } catch {
        // Keep defaults when stored settings are invalid.
      }
    }
  }, []);

  const save = (key: string, val: unknown) => {
    const s = { sensitivity, sound, theme, [key]: val };
    localStorage.setItem('vigil_settings', JSON.stringify(s));
  };

  return (
    <div className="page-wrap settings-page">
      <div className="page-heading">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Configure monitoring preferences</p>
        </div>
      </div>

      <section className="panel settings-section">
        <div className="panel-header">
          <div className="panel-title"><SlidersHorizontal size={16} /> SYSTEM PREFERENCES</div>
        </div>

        <SettingRow
          icon={<BrainCircuit />}
          title="Detection Sensitivity"
          description="Adjusts confidence threshold for events"
        >
          <div className="range-control">
            <input
              type="range"
              min="0"
              max="100"
              value={sensitivity}
              onChange={(e) => {
                const value = Number(e.target.value);
                setSensitivity(value);
                save('sensitivity', value);
              }}
            />
            <span className="mono">{sensitivity}</span>
          </div>
        </SettingRow>

        <SettingRow
          icon={<Volume2 />}
          title="Alert Sound"
          description="Play audio on critical events"
        >
          <button
            className={`toggle ${sound ? 'on' : ''}`}
            onClick={() => {
              const value = !sound;
              setSound(value);
              save('sound', value);
            }}
            aria-label="Toggle alert sound"
          >
            <span />
          </button>
        </SettingRow>

        <SettingRow
          icon={<Palette />}
          title="Theme"
          description="Dark mode recommended for automotive"
        >
          <select
            className="dark-select"
            value={theme}
            onChange={(e) => {
              setTheme(e.target.value);
              save('theme', e.target.value);
            }}
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </SettingRow>
      </section>

      <section className="panel settings-section">
        <div className="panel-header">
          <div className="panel-title"><Info size={16} /> ABOUT DRIVEGUARD AI</div>
        </div>
        <div className="architecture-grid">
          <div className="architecture-card">
            <span className="architecture-icon safe"><BrainCircuit size={18} /></span>
            <strong>REAL COMPONENTS</strong>
            <ul>
              <li>Local Webcam Stream</li>
              <li>Browser Face Detection</li>
              <li>Offline Application Shell</li>
            </ul>
          </div>
          <div className="architecture-card">
            <span className="architecture-icon attention"><Bell size={18} /></span>
            <strong>SIMULATED TELEMETRY</strong>
            <ul>
              <li>Eye Closure & Yawning</li>
              <li>Head Pose & Phone Usage</li>
              <li>Seatbelt Status</li>
              <li>Risk Score & Live Events</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

function SettingRow({ icon, title, description, children }: any) {
  return (
    <div className="setting-row">
      <div className="setting-info">
        <span className="setting-icon">{icon}</span>
        <div>
          <strong>{title}</strong>
          <span>{description}</span>
        </div>
      </div>
      {children}
    </div>
  );
}
