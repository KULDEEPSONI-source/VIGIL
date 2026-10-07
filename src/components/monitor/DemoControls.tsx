import { Play, RotateCcw, Pause } from 'lucide-react';
import { useTelemetry } from '../../hooks/useTelemetry';
import { telemetrySource } from '../../data';

export function DemoControls() {
  const frame = useTelemetry();

  if (!frame) return null;

  const state = telemetrySource.getState();
  const isPlaying = state.playing;

  return (
    <div className="demo-controls">
      {isPlaying ? (
        <button className="primary-button control-button" onClick={() => telemetrySource.pause()}>
          <Pause size={17} /> Pause Scenario
        </button>
      ) : (
        <button className="primary-button control-button" onClick={() => telemetrySource.start()}>
          <Play size={17} /> Resume Scenario
        </button>
      )}

      <button className="ghost-button control-button" onClick={() => telemetrySource.restart()}>
        <RotateCcw size={17} /> Reset
      </button>
    </div>
  );
}
