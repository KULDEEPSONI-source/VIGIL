
import { useTelemetry } from '../hooks/useTelemetry';
import { STATUS_COLORS, STATUS_LABELS } from '../config/risk';
import { CameraPanel } from '../components/monitor/CameraPanel';
import { DemoControls } from '../components/monitor/DemoControls';

export default function Dashboard() {
    const frame = useTelemetry();

    if (!frame) return <div style={{ padding: 24 }}>Loading...</div>;

    const statusColor = STATUS_COLORS[frame.risk.status];
    const statusLabel = STATUS_LABELS[frame.risk.status];

    return (
        <div style={{ display: 'grid', gridTemplateColumns: '60% calc(40% - 24px)', height: '100%', padding: '24px', gap: '24px', overflowY: 'auto' }}>
            {/* Left */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <CameraPanel />
                
                <div style={{ flex: 1, backgroundColor: 'var(--surface-1)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', padding: '16px' }}>
                    <h2 style={{ fontSize: '12px', color: 'var(--text-faint)', marginTop: 0 }}>LIVE EVENTS</h2>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {frame.newEvents.length === 0 && <div style={{ color: 'var(--text-dim)', fontSize: '14px' }}>No events yet. Monitoring is active.</div>}
                        {frame.newEvents.map((ev, i) => (
                            <div key={i} style={{ display: 'flex', gap: '12px', alignItems: 'center', padding: '8px', backgroundColor: 'var(--surface-2)', borderRadius: 'var(--radius-sm)' }}>
                                <span className="mono" style={{ color: 'var(--text-faint)', fontSize: '12px' }}>{ev.ts}</span>
                                <span style={{ color: STATUS_COLORS[ev.severity], fontSize: '18px' }}>•</span>
                                <span style={{ fontSize: '14px' }}>{ev.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
            
            {/* Right */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div style={{ backgroundColor: 'var(--surface-1)', padding: '32px', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <h2 style={{ color: 'var(--text-faint)', fontSize: '12px', margin: '0 0 16px 0', letterSpacing: '1px' }}>RISK SCORE</h2>
                    <div style={{ position: 'relative', width: '200px', height: '200px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                        <svg viewBox="0 0 100 100" style={{ position: 'absolute', width: '100%', height: '100%' }}>
                            <circle cx="50" cy="50" r="45" fill="none" stroke="var(--surface-2)" strokeWidth="10" strokeDasharray="212 282" strokeDashoffset="-35" strokeLinecap="round" />
                            <circle cx="50" cy="50" r="45" fill="none" stroke={statusColor} strokeWidth="10" strokeDasharray={`${(frame.risk.score / 100) * 212} 282`} strokeDashoffset="-35" strokeLinecap="round" style={{ transition: 'stroke-dasharray 0.5s ease-out, stroke 0.5s' }} />
                        </svg>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '-10px' }}>
                            <div className="mono" style={{ fontSize: '56px', color: statusColor, fontWeight: 700, lineHeight: 1 }}>
                                {Math.round(frame.risk.score)}
                            </div>
                            <div style={{ color: statusColor, fontWeight: 600, fontSize: '14px', marginTop: '4px' }}>
                                {statusLabel.toUpperCase()}
                            </div>
                        </div>
                    </div>
                    {frame.risk.topContributor && (
                        <div style={{ marginTop: '16px', fontSize: '14px', color: 'var(--text-dim)' }}>
                            Top contributor: <span style={{ color: 'var(--text)' }}>{frame.risk.topContributor}</span>
                        </div>
                    )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <DetectionCard title="EYE CLOSURE" active={frame.detections.eyeClosure} metric={frame.detections.metrics.ear?.toFixed(2)} activeColor="var(--high)" />
                    <DetectionCard title="YAWNING" active={frame.detections.yawning} metric={frame.detections.metrics.mar?.toFixed(2)} activeColor="var(--attention)" />
                    <DetectionCard title="HEAD POSE" active={frame.detections.headInstability} metric={`${frame.detections.metrics.yawDeg?.toFixed(0)}°`} activeColor="var(--critical)" />
                    <DetectionCard title="PHONE" active={frame.detections.phoneDetected} metric={`${frame.detections.metrics.phoneConfidence?.toFixed(0)}%`} activeColor="var(--critical)" />
                    <div style={{ gridColumn: '1 / -1' }}>
                        <DetectionCard title="SEATBELT" state={frame.detections.seatbelt} isMonitored={frame.detections.seatbelt !== "not_monitored"} activeColor="var(--critical)" />
                    </div>
                </div>
                <DemoControls />
            </div>
        </div>
    );
}

function DetectionCard({ title, active, state, isMonitored = true, metric, activeColor }: any) {
    const isActive = active || state === "not_detected";
    const bg = !isMonitored ? "transparent" : isActive ? `${activeColor}22` : "var(--surface-1)";
    const border = !isMonitored ? "1px dashed var(--border-strong)" : isActive ? `1px solid ${activeColor}` : "1px solid var(--border)";
    const color = !isMonitored ? "var(--text-faint)" : isActive ? activeColor : "var(--text)";
    const valueText = !isMonitored ? "NOT MONITORED" : active ? "DETECTED" : state === "not_detected" ? "NOT FASTENED" : state === "fastened" ? "FASTENED" : "NORMAL";

    return (
        <div style={{ padding: '16px', backgroundColor: bg, border: border, borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '8px', transition: 'all 0.2s' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-faint)', letterSpacing: '1px' }}>{title}</span>
                {metric && isMonitored && <span className="mono" style={{ fontSize: '12px', color: 'var(--text-dim)' }}>{metric}</span>}
            </div>
            <div style={{ fontSize: '14px', fontWeight: 600, color }}>
                {valueText}
            </div>
        </div>
    );
}
