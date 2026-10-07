import { useState, useEffect } from 'react';

export function Settings() {
    const [sensitivity, setSensitivity] = useState(50);
    const [sound, setSound] = useState(true);
    const [theme, setTheme] = useState("dark");

    useEffect(() => {
        const saved = localStorage.getItem("vigil_settings");
        if (saved) {
            try {
                const s = JSON.parse(saved);
                if (s.sensitivity) setSensitivity(s.sensitivity);
                if (s.sound !== undefined) setSound(s.sound);
                if (s.theme) setTheme(s.theme);
            } catch (e) {}
        }
    }, []);

    const save = (key: string, val: any) => {
        const s = { sensitivity, sound, theme, [key]: val };
        localStorage.setItem("vigil_settings", JSON.stringify(s));
    };

    return (
        <div style={{ padding: '24px', maxWidth: '800px' }}>
            <h2 style={{ fontSize: '24px', margin: '0 0 24px 0' }}>Settings</h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <section style={{ backgroundColor: 'var(--surface-1)', padding: '24px', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)' }}>
                    <h3 style={{ margin: '0 0 16px 0', fontSize: '16px' }}>System Preferences</h3>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
                        <div>
                            <div style={{ fontWeight: 'bold' }}>Detection Sensitivity</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-dim)' }}>Adjusts confidence threshold for events</div>
                        </div>
                        <input 
                            type="range" min="0" max="100" value={sensitivity} 
                            onChange={e => { setSensitivity(Number(e.target.value)); save('sensitivity', Number(e.target.value)); }} 
                        />
                    </div>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
                        <div>
                            <div style={{ fontWeight: 'bold' }}>Alert Sound</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-dim)' }}>Play audio on critical events</div>
                        </div>
                        <input 
                            type="checkbox" checked={sound} 
                            onChange={e => { setSound(e.target.checked); save('sound', e.target.checked); }} 
                        />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0' }}>
                        <div>
                            <div style={{ fontWeight: 'bold' }}>Theme</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-dim)' }}>Dark mode recommended for automotive</div>
                        </div>
                        <select 
                            value={theme} 
                            onChange={e => { setTheme(e.target.value); save('theme', e.target.value); }}
                            style={{ background: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-strong)', padding: '6px' }}
                        >
                            <option value="dark">Dark (Default)</option>
                            <option value="light">Light</option>
                        </select>
                    </div>
                </section>

                <section style={{ backgroundColor: 'var(--surface-1)', padding: '24px', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)' }}>
                    <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: 'var(--safe)' }}>About DriveGuard AI (Architecture Note)</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', fontSize: '14px' }}>
                        <div style={{ padding: '16px', background: 'var(--surface-2)', borderRadius: 'var(--radius-md)' }}>
                            <strong style={{ color: 'var(--safe)' }}>REAL COMPONENTS</strong>
                            <ul style={{ paddingLeft: '20px', color: 'var(--text-dim)', marginTop: '8px' }}>
                                <li>Local Webcam Stream</li>
                                <li>Browser Face Detection (when model loaded)</li>
                                <li>Offline Application Shell</li>
                            </ul>
                        </div>
                        <div style={{ padding: '16px', background: 'var(--surface-2)', borderRadius: 'var(--radius-md)' }}>
                            <strong style={{ color: 'var(--attention)' }}>SIMULATED TELEMETRY</strong>
                            <ul style={{ paddingLeft: '20px', color: 'var(--text-dim)', marginTop: '8px' }}>
                                <li>Eye Closure & Yawning</li>
                                <li>Head Pose & Phone Usage</li>
                                <li>Seatbelt Status</li>
                                <li>Risk Score & Live Events</li>
                            </ul>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
