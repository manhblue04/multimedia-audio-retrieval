import { useRef, useState } from "react";

const ACCEPTED = ".wav,.mp3,.ogg,.flac,.aiff,.m4a";

export default function AudioUploader({ onFile, disabled }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = (file) => {
    if (!file) return;
    onFile(file);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  return (
    <div
      onClick={() => !disabled && inputRef.current?.click()}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={() => setDragOver(false)}
      className={`
        relative flex flex-col items-center justify-center gap-4
        w-full max-w-lg mx-auto rounded-2xl border-2 border-dashed
        p-12 cursor-pointer select-none transition-all duration-300
        ${dragOver
          ? "border-brand-400 bg-brand-400/10 scale-105"
          : "border-white/20 bg-white/5 hover:border-brand-500/60 hover:bg-white/8"
        }
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
    >
      {/* Animated ring */}
      <div className={`relative w-24 h-24 flex items-center justify-center rounded-full bg-brand-600/20 ${dragOver ? "animate-pulse" : ""}`}>
        <div className="w-16 h-16 rounded-full bg-brand-500/30 flex items-center justify-center">
          <svg className="w-8 h-8 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
          </svg>
        </div>
      </div>

      <div className="text-center">
        <p className="text-lg font-semibold text-white">
          {dragOver ? "Thả file vào đây" : "Tải lên file âm thanh"}
        </p>
        <p className="text-sm text-white/50 mt-1">
          Kéo thả hoặc click để chọn · WAV, MP3, OGG, FLAC
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />
    </div>
  );
}
