import type { RiskStatus } from "../types/telemetry";

export const MOCK_SEATBELT_MONITORED = true;

export const RISK_THRESHOLDS = {
    SAFE_MAX: 29,
    ATTENTION_MAX: 49,
    HIGH_RISK_MAX: 74,
};

export function getStatus(score: number): RiskStatus {
    if (score <= RISK_THRESHOLDS.SAFE_MAX) return "SAFE";
    if (score <= RISK_THRESHOLDS.ATTENTION_MAX) return "ATTENTION";
    if (score <= RISK_THRESHOLDS.HIGH_RISK_MAX) return "HIGH_RISK";
    return "CRITICAL";
}

export const STATUS_COLORS = {
    SAFE: "var(--safe)",
    ATTENTION: "var(--attention)",
    HIGH_RISK: "var(--high)",
    CRITICAL: "var(--critical)",
};

export const STATUS_LABELS = {
    SAFE: "Safe",
    ATTENTION: "Attention",
    HIGH_RISK: "High Risk",
    CRITICAL: "Critical",
};
