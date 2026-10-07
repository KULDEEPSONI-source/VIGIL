import { CalendarDays, Clock3, ShieldCheck, AlertTriangle } from 'lucide-react';

const sessions = [
  { date: 'Oct 5, 2026', duration: '45m', avg: 24, max: 57, alerts: 2, status: 'SAFE' },
  { date: 'Oct 4, 2026', duration: '1h 20m', avg: 45, max: 76, alerts: 5, status: 'HIGH RISK' },
];

export function History() {
  return (
    <div className="page-wrap">
      <div className="page-heading">
        <div>
          <h1 className="page-title">Session History</h1>
          <p className="page-subtitle">Review previous monitoring sessions</p>
        </div>
        <div className="history-summary">
          <span><CalendarDays size={14} /> 18 sessions</span>
        </div>
      </div>

      <section className="panel history-panel">
        <div className="history-table-wrap">
          <table className="history-table">
            <thead>
              <tr>
                <th>DATE</th>
                <th>DURATION</th>
                <th>AVG RISK</th>
                <th>MAX RISK</th>
                <th>ALERTS</th>
                <th>FINAL STATUS</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.date}>
                  <td className="strong-cell">{session.date}</td>
                  <td><Clock3 size={14} /> {session.duration}</td>
                  <td className="mono">{session.avg}</td>
                  <td className="mono">{session.max}</td>
                  <td className="mono">{session.alerts}</td>
                  <td>
                    <span className={`status-badge ${session.status === 'SAFE' ? 'safe' : 'high'}`}>
                      {session.status === 'SAFE' ? <ShieldCheck size={13} /> : <AlertTriangle size={13} />}
                      {session.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
