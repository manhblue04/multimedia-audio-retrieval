/**
 * GroundTruthSelector — người dùng xác nhận nhạc cụ thật của file query
 * để tính Precision@5 client-side (không cần gọi API lại).
 *
 * Props:
 *   groundTruth: string — nhạc cụ đang chọn ("" nếu chưa chọn)
 *   onSelect: (instr: string) => void — toggle chọn/bỏ
 *   top5: Array<{instrument, similarity, ...}> — từ results.results
 */

const INSTRUMENTS = ["clarinet", "flute", "saxophone", "trumpet"];

const BADGE_COLORS = {
  clarinet:  "bg-purple-500/20 border-purple-500/50 text-purple-300",
  flute:     "bg-green-500/20  border-green-500/50  text-green-300",
  saxophone: "bg-amber-500/20  border-amber-500/50  text-amber-300",
  trumpet:   "bg-red-500/20    border-red-500/50    text-red-300",
};

const ACTIVE_COLORS = {
  clarinet:  "bg-purple-500/40 border-purple-400 text-purple-200",
  flute:     "bg-green-500/40  border-green-400  text-green-200",
  saxophone: "bg-amber-500/40  border-amber-400  text-amber-200",
  trumpet:   "bg-red-500/40    border-red-400    text-red-200",
};

/** Tính Precision@5 client-side */
function computePrecision(top5, groundTruth) {
  if (!groundTruth || !top5?.length) return null;
  const relevant = top5.filter((r) => r.instrument === groundTruth).length;
  return relevant / Math.min(5, top5.length);
}

export default function GroundTruthSelector({ groundTruth, onSelect, top5 }) {
  const precision = computePrecision(top5, groundTruth);

  return (
    <div className="glass rounded-2xl p-4 mb-4">
      <p className="text-xs text-white/40 uppercase tracking-widest mb-3">
        Xác nhận nhạc cụ thật (tính Precision@5)
      </p>

      <div className="flex items-center gap-2 flex-wrap">
        {INSTRUMENTS.map((instr) => {
          const isActive = groundTruth === instr;
          const colorClass = isActive ? ACTIVE_COLORS[instr] : BADGE_COLORS[instr];
          return (
            <button
              key={instr}
              onClick={() => onSelect(isActive ? "" : instr)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium capitalize border transition-all
                hover:scale-105 active:scale-95 ${colorClass}`}
            >
              {isActive && "✓ "}{instr}
            </button>
          );
        })}

        {precision !== null && (
          <div className="ml-auto flex items-center gap-1.5">
            <span className="text-xs text-white/40">Precision@5:</span>
            <span
              className={`text-sm font-bold ${
                precision >= 0.8
                  ? "text-green-400"
                  : precision >= 0.5
                  ? "text-amber-400"
                  : "text-red-400"
              }`}
            >
              {Math.round(precision * 100)}%
            </span>
            <span className="text-xs text-white/30">
              ({top5?.filter((r) => r.instrument === groundTruth).length}/
              {Math.min(5, top5?.length ?? 0)} đúng)
            </span>
          </div>
        )}
      </div>

      {!groundTruth && (
        <p className="text-xs text-white/25 mt-2">
          Chọn nhạc cụ để xem Precision@5 thực tế
        </p>
      )}
    </div>
  );
}
