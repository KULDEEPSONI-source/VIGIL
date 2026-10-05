import { useCamera } from '../../hooks/useCamera';
import { Camera, CameraOff, AlertCircle } from 'lucide-react';

export function CameraPanel() {
    const { isActive, error, startCamera, stopCamera, videoRef } = useCamera();

    return (
        <div style={{ height: '400px', backgroundColor: 'var(--surface-1)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', zIndex: 10, backgroundColor: 'rgba(17, 21, 28, 0.8)' }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-dim)' }}>CAMERA PREVIEW (REAL)</span>
                <span style={{ fontSize: '12px', color: 'var(--attention)', fontWeight: 'bold' }}>Face detection model unavailable</span>
            </div>
            
            <div style={{ flex: 1, position: 'relative', backgroundColor: '#000' }}>
                <video 
                    ref={videoRef} 
                    autoPlay 
                    playsInline 
                    muted 
                    style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)', display: isActive ? 'block' : 'none' }} 
                />
                
                {!isActive && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '16px' }}>
                        {error ? <AlertCircle size={48} color="var(--critical)" /> : <CameraOff size={48} color="var(--border-strong)" />}
                        <span style={{ color: error ? 'var(--critical)' : 'var(--text-dim)' }}>{error || "Camera is offline"}</span>
                        <button onClick={startCamera} style={{ padding: '8px 16px', background: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-sm)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Camera size={16} /> Start Camera
                        </button>
                    </div>
                )}
                
                {isActive && (
                    <button onClick={stopCamera} style={{ position: 'absolute', bottom: '16px', right: '16px', padding: '6px 12px', background: 'rgba(0,0,0,0.6)', color: 'var(--text)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-sm)', cursor: 'pointer', fontSize: '12px', zIndex: 10 }}>
                        Stop Camera
                    </button>
                )}
            </div>
            
            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '8px 16px', backgroundColor: 'rgba(0,0,0,0.7)', fontSize: '11px', color: 'var(--text-dim)', textAlign: 'center', zIndex: 10 }}>
                Camera preview: real browser webcam. Face detection: unavailable offline. Risk events: SIMULATED telemetry.
            </div>
        </div>
    );
}
