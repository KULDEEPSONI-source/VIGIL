export type RiskStatus = "SAFE" | "ATTENTION" | "HIGH_RISK" | "CRITICAL";
export type Trend = "rising" | "stable" | "falling";
export type SeatbeltState = "fastened" | "not_detected" | "not_monitored";

export interface Driver {
    id: string;
    name: string;
    avgRisk: number;
    sessions: number;
    totalAlerts: number;
}

export interface Contributor {
    key: "eyeClosure" | "phone" | "headMovement" | "yawning" | "seatbelt";
    label: string;
    sharePct: number;
}

export interface DetectionState {
    eyeClosure: boolean;
    yawning: boolean;
    headInstability: boolean;
    phoneDetected: boolean;
    seatbelt: SeatbeltState;
    metrics: {
        ear: number | null;
        mar: number | null;
        yawDeg: number | null;
        pitchDeg: number | null;
        phoneConfidence: number | null;
    };
}

export interface LiveEvent {
    id: string;
    ts: string;
    type: "yawn" | "eye_closure" | "head_instability" | "phone" | "seatbelt" | "recovery";
    label: string;
    severity: RiskStatus;
}

export interface TelemetryFrame {
    mode: "mock" | "live";
    connection: "connected" | "reconnecting" | "unavailable";
    timestamp: string;
    driver: { id: string; name: string } | null;
    session: { id: string; startedAt: string; elapsedSec: number };
    risk: {
        score: number;
        status: RiskStatus;
        trend: Trend;
        delta: number;
        contributors: Contributor[];
        topContributor: string | null;
    };
    detections: DetectionState;
    warning: { level: RiskStatus; title: string; message: string } | null;
    newEvents: LiveEvent[];
}

export interface SessionSummary {
    id: string;
    driverId: string;
    driverName: string;
    startedAt: string;
    endedAt: string;
    durationSec: number;
    avgRisk: number;
    maxRisk: number;
    totalAlerts: number;
    finalStatus: RiskStatus;
    drowsinessEvents: number;
    yawns: number;
    headAnomalies: number;
    phoneEvents: number;
    seatbeltViolations: number;
    contributors: Contributor[];
    riskSeries: number[];
}

export interface TelemetrySource {
    subscribe(cb: (f: TelemetryFrame) => void): () => void;
    start(): void;
    pause(): void;
    restart(): void;
    next(): void;
    reset(): void;
    selectDriver(id: string): void;
    getState(): { playing: boolean; stepIndex: number; stepCount: number };
}
