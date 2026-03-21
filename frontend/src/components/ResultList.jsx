import AudioPlayer from "./AudioPlayer";

const INSTRUMENT_COLORS = {
  clarinet: "from-purple-500/20 to-purple-900/10 border-purple-500/30",
  flute: "from-green-500/20 to-green-900/10 border-green-500/30",
  saxophone: "from-amber-500/20 to-amber-900/10 border-amber-500/30",
  trumpet: "from-red-500/20 to-red-900/10 border-red-500/30",
};

const INSTRUMENT_ICON = {
  clarinet: "🎵",
  flute: "🎶",
  saxophone: "🎷",
  trumpet: "🎺",
};

const INSTRUMENT_BADGE_COLOR = {
  clarinet: "bg-purple-500/20 text-purple-300 border-purple-500/40",
  flute: "bg-green-500/20 text-green-300 border-green-500/40",
  saxophone: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  trumpet: "bg-red-500/20 text-red-300 border-red-500/40",
};

function SimilarityBar({ score }) {
  const pct = Math.round(score * 1000) / 10; // 1 decimal: 0.995 → 99.5%
  const color =
    pct >= 90 ? "bg-green-400" : pct >= 70 ? "bg-brand-400" : pct >= 50 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-white/50">Độ tương đồng</span>
        <span className="font-semibold text-white">{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function ResultList({ results }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="w-full max-w-2xl mx-auto space-y-3">
      <h2 className="text-sm font-semibold text-white/40 uppercase tracking-widest text-center mb-4">
        Top {results.length} kết quả tương đồng
      </h2>
      {results.map((item, idx) => {
        const gradClass =
          INSTRUMENT_COLORS[item.instrument] ||
          "from-brand-500/20 to-brand-900/10 border-brand-500/30";
        const badgeClass =
          INSTRUMENT_BADGE_COLOR[item.instrument] ||
          "bg-brand-500/20 text-brand-300 border-brand-500/40";
        const icon = INSTRUMENT_ICON[item.instrument] || "🎵";

        return (
          <div
            key={idx}
            className={`relative glass rounded-2xl p-4 bg-gradient-to-br ${gradClass} border transition-transform hover:scale-[1.01]`}
          >
            {/* Rank badge */}
            <div className="absolute -top-2.5 -left-2.5 w-7 h-7 rounded-full bg-dark-900 border border-white/20 flex items-center justify-center text-xs font-bold text-white/80">
              {idx + 1}
            </div>

            <div className="flex items-start gap-3 mb-3">
              <span className="text-2xl">{icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded-full border capitalize ${badgeClass}`}
                  >
                    {item.instrument}
                  </span>
                  <span className="text-xs text-white/30">
                    {item.duration?.toFixed(1)}s · {(item.sample_rate / 1000).toFixed(0)}kHz
                  </span>
                </div>
                <p className="text-xs text-white/50 mt-1 truncate font-mono">
                  {item.file_name}
                </p>
              </div>
            </div>

            <SimilarityBar score={item.similarity} />

            {item.audio_url && (
              <div className="mt-3">
                <AudioPlayer audioUrl={item.audio_url} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
