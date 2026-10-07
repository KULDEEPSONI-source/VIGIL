import { UserRound, ShieldCheck, Activity, AlertTriangle } from 'lucide-react';

export function Profile() {
  return (
    <div className="page-wrap">
      <div className="page-heading">
        <div>
          <h1 className="page-title">Driver Profile</h1>
          <p className="page-subtitle">Safety profile and driving pattern</p>
        </div>
      </div>

      <section className="profile-hero panel">
        <div className="profile-avatar"><UserRound size={28} /></div>
        <div className="profile-main">
          <div className="profile-name">Rahul</div>
          <div className="profile-id mono">DR-001</div>
          <div className="profile-status"><span className="status-dot" /> Monitoring profile active</div>
        </div>
        <div className="profile-score">
          <span>AVERAGE RISK</span>
          <strong className="mono">34</strong>
        </div>
      </section>

      <div className="profile-grid">
        <Stat icon={<ShieldCheck />} label="Average Risk" value="34" />
        <Stat icon={<Activity />} label="Today's Risk" value="71 ↑" color="var(--high)" />
        <Stat icon={<UserRound />} label="Total Sessions" value="18" />
        <Stat icon={<AlertTriangle />} label="Total Alerts" value="27" color="var(--attention)" />
        <Stat icon={<Activity />} label="Drowsiness Events" value="34" color="var(--attention)" />
        <Stat icon={<AlertTriangle />} label="Distraction Events" value="19" color="var(--critical)" />
      </div>

      <section className="panel comparison-panel">
        <div className="panel-header">
          <div>
            <div className="panel-title">DRIVING PATTERN</div>
            <div className="chart-caption">Compared with your usual driving pattern</div>
          </div>
          <span className="comparison-value">+37 points</span>
        </div>
        <div className="profile-chart">
          <div className="profile-chart-line" />
          <div className="profile-chart-line second" />
        </div>
      </section>
    </div>
  );
}

function Stat({ icon, label, value, color = 'var(--text)' }: any) {
  return (
    <div className="panel stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-label">{label}</div>
      <div className="stat-value mono" style={{ color }}>{value}</div>
    </div>
  );
}
