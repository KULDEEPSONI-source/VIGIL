import type { TelemetrySource, TelemetryFrame, RiskStatus, Contributor } from "../types/telemetry";
import { getStatus, MOCK_SEATBELT_MONITORED } from "../config/risk";

export class MockTelemetrySource implements TelemetrySource {
    private listeners: ((f: TelemetryFrame) => void)[] = [];
    private interval: number | null = null;
    private stepIndex = 0;
    private playing = true;
    private currentScore = 12;
    private targetScore = 12;
    private tickCount = 0;
    private sessionStart = Date.now();
    
    // Scenario phases: target score, duration (ticks at 500ms), name
    private scenario = [
        { target: 12, ticks: 16, name: "Normal" }, // 8s
        { target: 28, ticks: 6, name: "Yawning" }, // 3s
        { target: 57, ticks: 8, name: "Eye Closure" }, // 4s
        { target: 76, ticks: 8, name: "Head Instability" }, // 4s
        { target: 92, ticks: 10, name: "Phone Usage" }, // 5s
        { target: 82, ticks: 6, name: "Recovery 1" },
        { target: 69, ticks: 6, name: "Recovery 2" },
        { target: 55, ticks: 6, name: "Recovery 3" },
        { target: 42, ticks: 6, name: "Recovery 4" },
        { target: 30, ticks: 6, name: "Recovery 5" },
        { target: 18, ticks: 6, name: "Recovery 6" },
        { target: 12, ticks: 10, name: "Baseline" },
    ];

    private currentPhase = this.scenario[0];
    private phaseTick = 0;
    
    private activeDetections = {
        yawning: false,
        eyeClosure: false,
        headInstability: false,
        phoneDetected: false
    };

    subscribe(cb: (f: TelemetryFrame) => void) {
        this.listeners.push(cb);
        return () => {
            this.listeners = this.listeners.filter(l => l !== cb);
        };
    }

    start() {
        this.playing = true;
        if (!this.interval) {
            this.interval = window.setInterval(() => this.tick(), 500);
        }
    }

    pause() {
        this.playing = false;
        if (this.interval) {
            window.clearInterval(this.interval);
            this.interval = null;
        }
    }

    restart() {
        this.reset();
        this.start();
    }

    next() {
        this.stepIndex = (this.stepIndex + 1) % this.scenario.length;
        this.currentPhase = this.scenario[this.stepIndex];
        this.phaseTick = 0;
        this.targetScore = this.currentPhase.target;
        this.tick();
    }

    reset() {
        this.stepIndex = 0;
        this.currentPhase = this.scenario[0];
        this.phaseTick = 0;
        this.currentScore = 12;
        this.targetScore = 12;
        this.tickCount = 0;
        this.sessionStart = Date.now();
        this.activeDetections = { yawning: false, eyeClosure: false, headInstability: false, phoneDetected: false };
    }

    selectDriver(_id: string) {
        this.reset();
        this.start();
    }

    getState() {
        return { playing: this.playing, stepIndex: this.stepIndex, stepCount: this.scenario.length };
    }

    private tick() {
        this.tickCount++;
        this.phaseTick++;
        
        if (this.phaseTick >= this.currentPhase.ticks) {
            this.stepIndex = (this.stepIndex + 1) % this.scenario.length;
            this.currentPhase = this.scenario[this.stepIndex];
            this.phaseTick = 0;
            this.targetScore = this.currentPhase.target;
        }

        // Interpolate score
        this.currentScore += (this.targetScore - this.currentScore) * 0.2;
        const noise = (Math.random() - 0.5) * 1.5;
        const score = Math.max(0, Math.min(100, this.currentScore + noise));
        
        // Update detections based on phase
        const name = this.currentPhase.name;
        this.activeDetections.yawning = name === "Yawning";
        this.activeDetections.eyeClosure = name === "Eye Closure" || (score > 50 && name.startsWith("Recovery") && score < 70);
        this.activeDetections.headInstability = name === "Head Instability";
        this.activeDetections.phoneDetected = name === "Phone Usage";
        
        const status = getStatus(score);
        
        const contributors: Contributor[] = [];
        if (this.activeDetections.phoneDetected) contributors.push({ key: "phone", label: "Phone Usage", sharePct: 45 });
        if (this.activeDetections.eyeClosure) contributors.push({ key: "eyeClosure", label: "Eye Closure", sharePct: 35 });
        if (this.activeDetections.headInstability) contributors.push({ key: "headMovement", label: "Head Movement", sharePct: 20 });
        if (this.activeDetections.yawning) contributors.push({ key: "yawning", label: "Yawning", sharePct: 15 });
        
        // normalize shares
        const total = contributors.reduce((s, c) => s + c.sharePct, 0);
        if (total > 0) {
            contributors.forEach(c => c.sharePct = Math.round((c.sharePct / total) * 100));
        }
        
        const topContributor = contributors.length > 0 ? contributors[0].label : null;
        
        const newEvents = [];
        if (this.phaseTick === 1) {
            if (name === "Yawning") newEvents.push({ id: `e${this.tickCount}`, ts: new Date().toLocaleTimeString(), type: "yawn", label: "Yawn detected", severity: "SAFE" as RiskStatus });
            if (name === "Eye Closure") newEvents.push({ id: `e${this.tickCount}`, ts: new Date().toLocaleTimeString(), type: "eye_closure", label: "Prolonged eye closure", severity: "HIGH_RISK" as RiskStatus });
            if (name === "Head Instability") newEvents.push({ id: `e${this.tickCount}`, ts: new Date().toLocaleTimeString(), type: "head_instability", label: "Head instability detected", severity: "CRITICAL" as RiskStatus });
            if (name === "Phone Usage") newEvents.push({ id: `e${this.tickCount}`, ts: new Date().toLocaleTimeString(), type: "phone", label: "Phone detected", severity: "CRITICAL" as RiskStatus });
        }

        const frame: TelemetryFrame = {
            mode: "mock",
            connection: "connected",
            timestamp: new Date().toISOString(),
            driver: { id: "DR-001", name: "Rahul" },
            session: { id: "sess-1", startedAt: new Date(this.sessionStart).toISOString(), elapsedSec: Math.floor((Date.now() - this.sessionStart) / 1000) },
            risk: {
                score,
                status,
                trend: this.targetScore > this.currentScore ? "rising" : this.targetScore < this.currentScore ? "falling" : "stable",
                delta: score - this.currentScore, // rough
                contributors,
                topContributor
            },
            detections: {
                ...this.activeDetections,
                seatbelt: MOCK_SEATBELT_MONITORED ? "fastened" : "not_monitored",
                metrics: {
                    ear: this.activeDetections.eyeClosure ? 0.1 : 0.3 + (Math.random()*0.05),
                    mar: this.activeDetections.yawning ? 0.8 : 0.1 + (Math.random()*0.05),
                    yawDeg: this.activeDetections.headInstability ? 35 : Math.random() * 5,
                    pitchDeg: this.activeDetections.headInstability ? 25 : Math.random() * 5,
                    phoneConfidence: this.activeDetections.phoneDetected ? 85 : 0
                }
            },
            warning: status === "ATTENTION" ? { level: status, title: "Attention", message: "Driver attention level decreased" } :
                     status === "HIGH_RISK" ? { level: status, title: "High Risk", message: "Prolonged eye closure detected" } :
                     status === "CRITICAL" ? { level: status, title: "Critical", message: "Phone usage detected while driving" } : null,
            newEvents: newEvents as any[]
        };

        this.listeners.forEach(cb => cb(frame));
    }
}
