/**
 * OodWarning — cảnh báo khi file có khả năng không phải nhạc cụ hơi.
 * Kích hoạt khi results.low_confidence === true
 * (cosine similarity của Top-1 < OOD_THRESHOLD).
 */
export default function OodWarning({ results }) {
  if (!results?.low_confidence) return null;

  const bestSim  = results.results?.[0]?.similarity ?? 0;
  const threshold = results.ood_threshold ?? 0.60;

  return (
    <div className="glass rounded-2xl p-4 mb-4 border border-amber-500/40 bg-amber-500/10">
      <div className="flex items-start gap-3">
        <span className="text-amber-400 text-xl flex-shrink-0">⚠️</span>
        <div className="flex-1">
          <p className="text-amber-300 font-semibold text-sm">
            File có thể không phải nhạc cụ hơi bộ
          </p>

          <div className="mt-2 flex items-center gap-2 text-xs text-amber-200/70">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
            Độ tương đồng cosine cao nhất chỉ đạt{" "}
            <span className="font-bold text-amber-300 mx-1">
              {Math.round(bestSim * 100)}%
            </span>
            (ngưỡng: {Math.round(threshold * 100)}%)
          </div>

          <p className="text-amber-200/50 text-xs mt-2">
            💡 Thử file solo nhạc cụ hơi sạch (~3–10s), không có nhạc nền hoặc tiếng ồn lớn.
          </p>
        </div>
      </div>
    </div>
  );
}
