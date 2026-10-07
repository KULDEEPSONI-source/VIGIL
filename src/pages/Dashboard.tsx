import {
  Activity,
  Eye,
  Smartphone,
  UserRound,
  ShieldCheck,
  FileText,
  List,
} from 'lucide-react';
import { useTelemetry } from '../hooks/useTelemetry';
import { STATUS_COLORS, STATUS_LABELS } from '../config/risk';
import { CameraPanel } from '../components/monitor/CameraPanel';
import { DemoControls } from '../components/monitor/DemoControls';

export default function Dashboard() {
  const frame = useTelemetry();

  if (!frame) {
    return (
      <div className="page-wrap">
        <div className="panel loading-panel">
          <Activity size={18} />
          <span>Connecting to live telemetry...</span>
        </div>
      </div>
    );
  }

  const statusColor = STATUS_COLORS[frame.risk.status];
  const statusLabel = STATUS_LABELS[frame.risk.status];

  return (
    <div className="dashboard-page">
      <div className="dashboard-grid">
        <section className="dashboard-left">
          <CameraPanel />

          <div className="panel events-panel">
            <div className="panel-header">
              <div className="panel-title">
                <List size={16} className="safe-icon" />
                LIVE EVENTS
              </div>
              <div className="monitoring-state">
                <span className="status-dot" />
                Monitoring is active
              </div>
            </div>

            <div className="events-body">
              {frame.newEvents.length === 0 ? (
                <div className="empty-events">
                  <div className="empty-icon"><FileText size={30} /></div>
                  <strong>No events yet</strong>
                  <span>Monitoring is active. Events will appear here in real-time.</span>
                </div>
              ) : (
                <div className="event-list">
                  {frame.newEvents.map((event, index) => (
                    <div className="event-row" key={`${event.ts}-${index}`}>
                      <span className="event-time mono">{event.ts}</span>
                      <span
                        className="event-severity"
                        style={{ color: STATUS_COLORS[event.severity] }}
                      />
                      <span>{event.label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="dashboard-right">
          <div
            className="panel risk-panel"
            style={{ '--risk-color': statusColor } as React.CSSProperties}
          >
            <div className="risk-header">
              <div className="panel-title">
                <ShieldCheck size={18} />
                RISK SCORE
              </div>
              <span className="analysis-pill">
                <span className="status-dot" />
                Live Analysis
              </span>
            </div>

            <div className="risk-gauge">
              <svg viewBox="0 0 120 120" aria-hidden="true">
                <circle
                  cx="60"
                  cy="60"
                  r="49"
                  className="gauge-track"
                  pathLength="100"
                />
                <circle
                  cx="60"
                  cy="60"
                  r="49"
                  className="gauge-value"
                  pathLength="100"
                  strokeDasharray={`${frame.risk.score} 100`}
                />
              </svg>

              <div className="risk-value">
                <strong className="mono">{Math.round(frame.risk.score)}</strong>
                <span>{statusLabel.toUpperCase()}</span>
              </div>
            </div>

            {frame.risk.topContributor && (
              <div className="risk-contributor">
                Top contributor <strong>{frame.risk.topContributor}</strong>
              </div>
            )}
          </div>

          <div className="detection-grid">
            <DetectionCard
              icon={<Eye />}
              title="EYE CLOSURE"
              active={frame.detections.eyeClosure}
              metric={frame.detections.metrics.ear?.toFixed(2)}
              activeColor="var(--high)"
            />
            <DetectionCard
              icon={<Activity />}
              title="YAWNING"
              active={frame.detections.yawning}
              metric={frame.detections.metrics.mar?.toFixed(2)}
              activeColor="var(--attention)"
            />
            <DetectionCard
              icon={<UserRound />}
              title="HEAD POSE"
              active={frame.detections.headInstability}
              metric={
                frame.detections.metrics.yawDeg !== undefined
                  ? `${frame.detections.metrics.yawDeg.toFixed(0)}°`
                  : undefined
              }
              activeColor="var(--critical)"
            />
            <DetectionCard
              icon={<Smartphone />}
              title="PHONE"
              active={frame.detections.phoneDetected}
              metric={
                frame.detections.metrics.phoneConfidence !== undefined
                  ? `${frame.detections.metrics.phoneConfidence.toFixed(0)}%`
                  : undefined
              }
              activeColor="var(--critical)"
            />
            <div className="detection-wide">
              <DetectionCard
                icon={<ShieldCheck />}
                title="SEATBELT"
                state={frame.detections.seatbelt}
                isMonitored={frame.detections.seatbelt !== 'not_monitored'}
                activeColor="var(--critical)"
              />
            </div>
          </div>

          <DemoControls />
        </section>
      </div>
    </div>
  );
}

function DetectionCard({
  icon,
  title,
  active,
  state,
  isMonitored = true,
  metric,
  activeColor,
}: {
  icon: React.ReactNode;
  title: string;
  active?: boolean;
  state?: string;
  isMonitored?: boolean;
  metric?: string;
  activeColor: string;
}) {
  const isActive = Boolean(active) || state === 'not_detected';

  const valueText = !isMonitored
    ? 'NOT MONITORED'
    : active
      ? 'DETECTED'
      : state === 'not_detected'
        ? 'NOT FASTENED'
        : state === 'fastened'
          ? 'FASTENED'
          : 'NORMAL';

  return (
    <div
      className={`detection-card ${isActive ? 'alert' : ''} ${!isMonitored ? 'unmonitored' : ''}`}
      style={{ '--active-color': activeColor } as React.CSSProperties}
    >
      <div className="detection-top">
        <div className="detection-title">
          {icon}
          <span>{title}</span>
        </div>
        {metric && isMonitored && <span className="metric mono">{metric}</span>}
      </div>
      <div className="detection-value">{valueText}</div>
      {!isActive && isMonitored && <div className="mini-spark" />}
    </div>
  );
}
