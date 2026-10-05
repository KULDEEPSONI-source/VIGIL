export function Profile() {
    return (
        <div style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '24px', margin: '0 0 24px 0' }}>Driver Profile</h2>
            <div style={{ backgroundColor: 'var(--surface-1)', padding: '32px', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)' }}>
                <h3 style={{ fontSize: '20px', margin: '0 0 16px 0', color: 'var(--safe)' }}>Rahul / DR-001</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                    <StatBox label="Average Risk" value="34" />
                    <StatBox label="Today's Risk" value="71 ↑" color="var(--high)" />
                    <StatBox label="Total Sessions" value="18" />
                    <StatBox label="Total Alerts" value="27" />
                    <StatBox label="Drowsiness Events" value="34" color="var(--attention)" />
                    <StatBox label="Distraction Events" value="19" color="var(--critical)" />
                </div>
                
                <div style={{ marginTop: '32px', paddingTop: '32px', borderTop: '1px solid var(--border)' }}>
                    <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-faint)' }}>Compared with your usual driving pattern</h4>
                    <p style={{ margin: 0, fontSize: '14px' }}>Today is 37 points above your average.</p>
                    <div style={{ height: '150px', backgroundColor: 'var(--surface-2)', marginTop: '16px', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>
                        [Historical Risk Chart Placeholder]
                    </div>
                </div>
            </div>
        </div>
    );
}

function StatBox({ label, value, color = "var(--text)" }: { label: string, value: string, color?: string }) {
    return (
        <div style={{ padding: '16px', backgroundColor: 'var(--surface-2)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-faint)' }}>{label}</div>
            <div className="mono" style={{ fontSize: '24px', fontWeight: 'bold', color, marginTop: '8px' }}>{value}</div>
        </div>
    );
}
