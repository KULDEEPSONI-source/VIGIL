import { MockTelemetrySource } from "./mockTelemetrySource";
export const telemetrySource = new MockTelemetrySource();
telemetrySource.start();
