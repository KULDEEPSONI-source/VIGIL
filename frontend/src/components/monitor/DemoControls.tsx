import { Play, RotateCcw } from 'lucide-react';
import { useTelemetry } from '../../hooks/useTelemetry';
import { telemetrySource } from '../../data';

export function DemoControls() {
    const frame = useTelemetry();
    
    if (!frame) return null;

    const state = telemetrySource.getState();
    const isPlaying = state.playing;

    return (
        <div style={{ display: 'flex', gap: '12px', marginTop: '16px', justifyContent: 'center' }}>
            {isPlaying ? (
                <button onClick={() => telemetrySource.pause()} style={{ padding: '12px 24px', background: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold' }}>
                    Pause Scenario
                </button>
            ) : (
                <button onClick={() => telemetrySource.start()} style={{ padding: '12px 24px', background: 'var(--safe-bg)', color: 'var(--safe)', border: '1px solid var(--safe)', borderRadius: 'var(--radius-md)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold' }}>
                    <Play size={18} /> Resume Scenario
                </button>
            )}
            <button onClick={() => telemetrySource.restart()} style={{ padding: '12px 24px', background: 'transparent', color: 'var(--text-dim)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <RotateCcw size={18} /> Reset
            </button>
        </div>
    );
}
