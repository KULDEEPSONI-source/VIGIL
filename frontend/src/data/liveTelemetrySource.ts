import type { TelemetryFrame, TelemetrySource } from "../types/telemetry";

export class LiveTelemetrySource implements TelemetrySource {
    private callbacks: ((f: TelemetryFrame) => void)[] = [];
    private intervalId: any = null;

    subscribe(cb: (f: TelemetryFrame) => void): () => void {
        this.callbacks.push(cb);
        return () => {
            this.callbacks = this.callbacks.filter(c => c !== cb);
        };
    }

    start(): void {
        if (this.intervalId) return;
        this.intervalId = setInterval(async () => {
            try {
                const res = await fetch("http://localhost:5000/api/telemetry");
                if (res.ok) {
                    const data = await res.json();
                    if (data.status !== "starting") {
                        this.callbacks.forEach(cb => cb(data as TelemetryFrame));
                    }
                }
            } catch (err) {
                // Ignore connection errors if server is down
            }
        }, 100); // 10 fps telemetry
    }

    pause(): void {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    restart(): void {}
    next(): void {}
    reset(): void {}
    selectDriver(id: string): void {}
    getState(): { playing: boolean; stepIndex: number; stepCount: number } {
        return { playing: !!this.intervalId, stepIndex: 0, stepCount: 1 };
    }
}
