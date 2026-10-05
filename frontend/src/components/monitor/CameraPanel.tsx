import { useState } from 'react';

export function CameraPanel() {
    const [hasError, setHasError] = useState(false);

    return (
        <div style={{ height: '400px', backgroundColor: 'var(--surface-1)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', zIndex: 10, backgroundColor: 'rgba(17, 21, 28, 0.8)' }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-dim)' }}>CAMERA PREVIEW (LIVE STREAM)</span>
                {hasError && <span style={{ fontSize: '12px', color: 'var(--attention)', fontWeight: 'bold' }}>Stream unavailable</span>}
            </div>
            
            <div style={{ flex: 1, position: 'relative', backgroundColor: '#000' }}>
                <img 
                    src="http://localhost:5000/video_feed" 
                    alt="Live Video Feed"
                    onError={() => setHasError(true)}
                    onLoad={() => setHasError(false)}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: hasError ? 'none' : 'block' }} 
                />
                
                {hasError && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '16px' }}>
                        <span style={{ color: 'var(--text-dim)' }}>Waiting for Python Backend (server.py)...</span>
                    </div>
                )}
            </div>
            
            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '8px 16px', backgroundColor: 'rgba(0,0,0,0.7)', fontSize: '11px', color: 'var(--text-dim)', textAlign: 'center', zIndex: 10 }}>
                Live Stream connected to Python backend. AI detection running on server.
            </div>
        </div>
    );
}
