import { Activity, AlertTriangle, Gauge, TrendingUp } from 'lucide-react';

const trend = [42, 35, 49, 38, 56, 47, 34, 41, 31, 36, 28, 34];

export function Analytics() {
  return (
    <div className="page-wrap">
      <div className="page-heading">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">Driving performance and safety insights</p>
        </div>
        <span className="analysis-pill"><span className="status-dot" /> Last 7 days</span>
      </div>

      <div className="kpi-grid">
        <KPI icon={<Gauge />} label="Average Risk" value="34" />
        <KPI icon={<TrendingUp />} label="Maximum Risk" value="76" color="var(--high)" />
        <KPI icon={<AlertTriangle />} label="Total Alerts" value="27" color="var(--attention)" />
        <KPI icon={<Activity />} label="Drowsiness" value="3.2/hr" color="var(--attention)" />
        <KPI icon={<Activity />} label="Distraction" value="1.8/hr" color="var(--critical)" />
        <KPI icon={<ShieldIcon />} label="Top Contributor" value="Eye Closure" />
      </div>

      <div className="analytics-grid">
        <section className="panel chart-panel">
          <div className="panel-header">
            <div>
              <div className="panel-title">RISK TREND</div>
              <div className="chart-caption">Recent session risk score</div>
            </div>
            <span className="chart-range">7D</span>
          </div>
          <div className="chart-area">
            <div className="chart-grid-lines">
              <span /><span /><span /><span />
            </div>
            <svg viewBox="0 0 600 220" preserveAspectRatio="none">
              <defs>
                <linearGradient id="riskFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#3ee8a1" stopOpacity="0.24" />
                  <stop offset="100%" stopColor="#3ee8a1" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path
                d={areaPath(trend)}
                fill="url(#riskFill)"
              />
              <path
                d={linePath(trend)}
                fill="none"
                stroke="#3ee8a1"
                strokeWidth="3"
                vectorEffect="non-scaling-stroke"
              />
            </svg>
          </div>
          <div className="chart-labels">
            {['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'].map((d) => <span key={d}>{d}</span>)}
          </div>
        </section>

        <section className="panel contributor-panel">
          <div className="panel-header">
            <div>
              <div className="panel-title">CONTRIBUTOR BREAKDOWN</div>
              <div className="chart-caption">Detected risk sources</div>
            </div>
          </div>
          <div className="contributor-body">
            <div className="donut">
              <div className="donut-inner">
                <strong>100%</strong>
                <span>ANALYSED</span>
              </div>
            </div>
            <div className="legend">
              <Legend label="Eye Closure" value="42%" color="var(--high)" />
              <Legend label="Head Pose" value="24%" color="var(--critical)" />
              <Legend label="Yawning" value="19%" color="var(--attention)" />
              <Legend label="Phone" value="15%" color="var(--safe)" />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function KPI({ icon, label, value, color = 'var(--text)' }: any) {
  return (
    <div className="panel kpi-card">
      <div className="kpi-icon">{icon}</div>
      <div>
        <div className="kpi-label">{label}</div>
        <div className="kpi-value mono" style={{ color }}>{value}</div>
      </div>
    </div>
  );
}

function Legend({ label, value, color }: any) {
  return (
    <div className="legend-row">
      <span className="legend-name"><i style={{ background: color }} />{label}</span>
      <strong className="mono">{value}</strong>
    </div>
  );
}

function ShieldIcon() {
  return <span className="shield-placeholder">◈</span>;
}

function linePath(values: number[]) {
  const min = 20;
  const max = 60;
  return values.map((v, i) => {
    const x = (i / (values.length - 1)) * 600;
    const y = 205 - ((v - min) / (max - min)) * 170;
    return `${i === 0 ? 'M' : 'L'} ${x} ${Math.max(15, Math.min(205, y))}`;
  }).join(' ');
}

function areaPath(values: number[]) {
  return `${linePath(values)} L 600 220 L 0 220 Z`;
}
