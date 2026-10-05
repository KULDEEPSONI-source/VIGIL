import { useState, useEffect } from "react";
import { telemetrySource } from "../data";
import type { TelemetryFrame } from "../types/telemetry";

export function useTelemetry() {
    const [frame, setFrame] = useState<TelemetryFrame | null>(null);

    useEffect(() => {
        return telemetrySource.subscribe(setFrame);
    }, []);

    return frame;
}
