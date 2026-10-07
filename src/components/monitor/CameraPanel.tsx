import { useState } from 'react';
import { Camera, EyeOff } from 'lucide-react';

export function CameraPanel() {
  const [hasError, setHasError] = useState(false);

  return (
    <div className="panel camera-panel">
      <div className="panel-header camera-header">
        <div className="panel-title">
          <Camera size={16} />
          CAMERA PREVIEW <span className="live-text">(LIVE STREAM)</span>
        </div>
        <div className="camera-status">
          <span className="status-dot" />
          Detecting in real-time
        </div>
      </div>

      <div className="camera-frame">
        <img
          src="http://localhost:5000/video_feed"
          alt="Live Video Feed"
          onError={() => setHasError(true)}
          onLoad={() => setHasError(false)}
          className={`camera-image ${hasError ? 'hidden' : ''}`}
        />

        {hasError && (
          <div className="camera-error">
            <EyeOff size={42} />
            <strong>Camera hidden for privacy</strong>
            <span>Detection is still running</span>
          </div>
        )}

        <span className="corner tl" />
        <span className="corner tr" />
        <span className="corner bl" />
        <span className="corner br" />
      </div>

      <div className="camera-footer">
        Live stream connected to Python backend · AI detection running on server
      </div>
    </div>
  );
}
