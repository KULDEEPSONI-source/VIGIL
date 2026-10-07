export function History() {
    return (
        <div style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '24px', margin: '0 0 24px 0' }}>Session History</h2>
            <div style={{ backgroundColor: 'var(--surface-1)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border)', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text-faint)', fontSize: '12px' }}>
                            <th style={{ padding: '16px' }}>Date</th>
                            <th style={{ padding: '16px' }}>Duration</th>
                            <th style={{ padding: '16px' }}>Average Risk</th>
                            <th style={{ padding: '16px' }}>Maximum Risk</th>
                            <th style={{ padding: '16px' }}>Alerts</th>
                            <th style={{ padding: '16px' }}>Final Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style={{ borderTop: '1px solid var(--border)', fontSize: '14px' }}>
                            <td style={{ padding: '16px' }}>Oct 5, 2026</td>
                            <td style={{ padding: '16px' }}>45m</td>
                            <td style={{ padding: '16px' }}>24</td>
                            <td style={{ padding: '16px' }}>57</td>
                            <td style={{ padding: '16px' }}>2</td>
                            <td style={{ padding: '16px' }}><span style={{ color: 'var(--safe)', background: 'var(--safe-bg)', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold', fontSize: '12px' }}>SAFE</span></td>
                        </tr>
                        <tr style={{ borderTop: '1px solid var(--border)', fontSize: '14px' }}>
                            <td style={{ padding: '16px' }}>Oct 4, 2026</td>
                            <td style={{ padding: '16px' }}>1h 20m</td>
                            <td style={{ padding: '16px' }}>45</td>
                            <td style={{ padding: '16px' }}>76</td>
                            <td style={{ padding: '16px' }}>5</td>
                            <td style={{ padding: '16px' }}><span style={{ color: 'var(--high)', background: 'var(--high-bg)', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold', fontSize: '12px' }}>HIGH RISK</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}
