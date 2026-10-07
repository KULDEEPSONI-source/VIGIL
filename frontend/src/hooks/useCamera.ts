import { useState, useEffect, useRef } from 'react';

export function useCamera() {
    const [stream, setStream] = useState<MediaStream | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isActive, setIsActive] = useState(false);
    const videoRef = useRef<HTMLVideoElement | null>(null);

    const startCamera = async () => {
        try {
            setError(null);
            const mediaStream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 1280, height: 720, facingMode: "user" } 
            });
            setStream(mediaStream);
            setIsActive(true);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
        } catch (err: any) {
            setError(err.message || "Failed to access camera");
            setIsActive(false);
        }
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
        setIsActive(false);
    };

    useEffect(() => {
        return () => stopCamera(); // Cleanup on unmount
    }, [stream]);

    return { stream, error, isActive, startCamera, stopCamera, videoRef };
}
