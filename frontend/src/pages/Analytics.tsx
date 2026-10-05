export function Analytics() {
    return (
        <div style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '24px', margin: '0 0 24px 0' }}>Analytics Dashboard</h2>
            <div style={{ backgroundColor: 'var(--surface-1)', padding: '32px', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
                    <KPIBox label="Average Risk" value="34" />
                    <KPIBox label="Maximum Risk" value="76" color="var(--high)" />
                    <KPIBox label="Total Alerts" value="27" />
                    <KPIBox label="Drowsiness Frequency" value="3.2/hr" color="var(--attention)" />
                    <KPIBox label="Distraction Frequency" value="1.8/hr" color="var(--critical)" />
                    <KPIBox label="Most Common Contributor" value="Eye Closure" color="var(--text)" />
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                    <div style={{ padding: '16px', backgroundColor: 'var(--surface-2)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                        <h4 style={{ margin: '0 0 16px 0', color: 'var(--text-dim)' }}>Risk Trend (Last 7 Days)</h4>
                        <div style={{ height: '150px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-faint)', border: '1px dashed var(--border-strong)' }}>
                            [Trend Chart Placeholder]
                        </div>
                    </div>
                    <div style={{ padding: '16px', backgroundColor: 'var(--surface-2)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                        <h4 style={{ margin: '0 0 16px 0', color: 'var(--text-dim)' }}>Contributor Breakdown</h4>
                        <div style={{ height: '150px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-faint)', border: '1px dashed var(--border-strong)' }}>
                            [Donut Chart Placeholder]
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function KPIBox({ label, value, color = "var(--text)" }: { label: string, value: string, color?: string }) {
    return (
        <div style={{ padding: '16px', backgroundColor: 'var(--surface-2)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-faint)' }}>{label}</div>
            <div className="mono" style={{ fontSize: '24px', fontWeight: 'bold', color, marginTop: '8px' }}>{value}</div>
        </div>
    );
}
