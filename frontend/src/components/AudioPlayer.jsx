import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";

export default function AudioPlayer({ audioUrl, label }) {
  const containerRef = useRef(null);
  const wsRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [ready, setReady] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    if (!containerRef.current || !audioUrl) return;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "rgba(66, 153, 225, 0.4)",
      progressColor: "rgba(66, 153, 225, 0.9)",
      cursorColor: "#4299e1",
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      height: 48,
      normalize: true,
      interact: true,
    });

    ws.load(audioUrl);
    ws.on("ready", () => {
      setReady(true);
      setDuration(ws.getDuration());
    });
    ws.on("audioprocess", () => setCurrentTime(ws.getCurrentTime()));
    ws.on("finish", () => setPlaying(false));
    ws.on("error", () => setReady(false));

    wsRef.current = ws;
    return () => {
      ws.destroy();
      wsRef.current = null;
      setReady(false);
      setPlaying(false);
    };
  }, [audioUrl]);

  const togglePlay = () => {
    if (!wsRef.current || !ready) return;
    wsRef.current.playPause();
    setPlaying((p) => !p);
  };

  const fmt = (s) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex items-center gap-3 w-full">
      <button
        onClick={togglePlay}
        disabled={!ready}
        className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-all
          ${ready
            ? "bg-brand-500 hover:bg-brand-400 cursor-pointer"
            : "bg-white/10 cursor-not-allowed opacity-50"
          }`}
      >
        {playing ? (
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
          </svg>
        ) : (
          <svg className="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </button>

      <div className="flex-1 min-w-0">
        {label && <p className="text-xs text-white/50 mb-1 truncate">{label}</p>}
        <div ref={containerRef} className="w-full" />
        {duration > 0 && (
          <div className="flex justify-between text-xs text-white/30 mt-0.5">
            <span>{fmt(currentTime)}</span>
            <span>{fmt(duration)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
