/**
 * IntermediateResults — Tab "Kết quả Trung Gian"
 * Hiển thị 3 section:
 *   1. Sliding Window Analysis
 *   2. Feature Vector — 16 nhóm, Raw vs Normalized
 *   3. Phân phối Cosine Similarity toàn DB (histogram)
 *
 * Props:
 *   intermediate: object — từ results.intermediate
 *   queryInfo: object — từ results.query
 *   topResult: object — results.results[0]
 */

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Cell,
} from "recharts";

// Tên ngắn cho 13 nhóm đặc trưng (v5: bỏ Chroma + Tonnetz)
const SHORT_NAMES = {
  "MFCC mean":          "MFCC μ",
  "MFCC std":           "MFCC σ",
  "Δ MFCC mean":        "ΔMFCC μ",
  "Δ MFCC std":         "ΔMFCC σ",
  "ΔΔ MFCC mean":       "ΔΔ μ",
  "Spectral Centroid":  "S.Cent",
  "Spectral Bandwidth": "S.BW",
  "Spectral Rolloff":   "Rolloff",
  "Spectral Flatness":  "Flat",
  "RMS Energy":         "RMS",
  "ZCR":                "ZCR",
  "Spectral Contrast":  "S.Cont",
  "Pitch F0":           "F0 🎵",
};

const INST_COLORS = {
  clarinet:  "#a78bfa",
  flute:     "#34d399",
  saxophone: "#fbbf24",
  trumpet:   "#f87171",
};

const CHART_STYLE = {
  contentStyle: { background: "#0f172a", border: "1px solid rgba(66,153,225,0.2)", borderRadius: 8 },
  labelStyle: { color: "#ffffff", fontSize: 12 },
  itemStyle: { color: "#ffffff", fontSize: 11 },
};

// ─────────────────────────────────────────────
// Section 1: Sliding Window
// ─────────────────────────────────────────────
function WindowSection({ intermediate, queryInfo }) {
  const { windows_count, window_max_similarities } = intermediate;
  const duration = queryInfo?.duration ?? 0;

  const data = (window_max_similarities ?? []).map((sim, i) => ({
    name: `Win ${i + 1}`,
    "Cosine max": Math.round(sim * 1000) / 10,
  }));

  const bestIdx = data.reduce(
    (best, d, i) => (d["Cosine max"] > (data[best]?.["Cosine max"] ?? 0) ? i : best),
    0
  );

  return (
    <div className="glass rounded-2xl p-4 mb-4">
      <p className="text-xs text-white/40 uppercase tracking-widest mb-1">
        🪟 Sliding Window Analysis
      </p>
      <p className="text-xs text-white/30 mb-4">
        File dài {duration.toFixed(2)}s →{" "}
        {windows_count === 1
          ? "1 window (file ≤ 3s, dùng toàn bộ)"
          : `${windows_count} cửa sổ 3s, gối 1.5s`}
        . Retrieval dùng similarity cao nhất qua tất cả windows.
      </p>

      {windows_count === 1 ? (
        <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
          <span className="text-brand-400 text-lg">✓</span>
          <span className="text-sm text-white/70">
            1 window — similarity:{" "}
            <span className="font-bold text-brand-300">
              {Math.round((window_max_similarities?.[0] ?? 0) * 100)}%
            </span>
          </span>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={40 + windows_count * 36}>
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 30 }}>
            <XAxis
              type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 10, fill: "#94a3b8" }}
            />
            <YAxis
              type="category" dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} width={44}
            />
            <Tooltip
              {...CHART_STYLE}
              formatter={(v) => [`${v}%`, "Cosine max"]}
            />
            <Bar dataKey="Cosine max" radius={4}>
              {data.map((_, i) => (
                <Cell
                  key={i}
                  fill={i === bestIdx ? "#4299e1" : "rgba(66,153,225,0.4)"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
      {windows_count > 1 && (
        <p className="text-xs text-white/25 mt-2">
          Cột xanh đậm = window cho kết quả tốt nhất.
        </p>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Section 2: Feature Groups
// ─────────────────────────────────────────────
function FeatureSection({ intermediate }) {
  const summary = intermediate?.feature_group_summary ?? [];
  if (!summary.length) return null;

  const data = summary.map((g) => ({
    name: SHORT_NAMES[g.name] || g.name,
    "Raw": parseFloat(g.raw_abs_mean.toFixed(3)),
    "Normalized": parseFloat(g.norm_abs_mean.toFixed(4)),
  }));

  // Tìm nhóm F0 để highlight
  const f0Idx = summary.findIndex((g) => g.name === "Pitch F0");

  return (
    <div className="glass rounded-2xl p-4 mb-4">
      <p className="text-xs text-white/40 uppercase tracking-widest mb-1">
        📊 Feature Vector — 13 nhóm × 123 chiều
      </p>
      <p className="text-xs text-white/30 mb-4">
        Raw = giá trị thô từ librosa (đơn vị khác nhau, ví dụ F0 ~300–800 Hz).
        Normalized = sau StandardScaler + L2 norm → đồng đơn vị, dùng cho cosine similarity.
      </p>

      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ bottom: 44, right: 8 }}>
          <XAxis
            dataKey="name"
            tick={{ fontSize: 9, fill: "#94a3b8" }}
            angle={-40}
            textAnchor="end"
            interval={0}
          />
          <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
          <Tooltip
            {...CHART_STYLE}
            formatter={(v, name) => [v, name]}
          />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
          <Bar dataKey="Raw" name="Raw" fill="#e2a03f" radius={2} opacity={0.8} />
          <Bar dataKey="Normalized" name="Normalized" fill="#4299e1" radius={2} />
        </BarChart>
      </ResponsiveContainer>

      {f0Idx >= 0 && (
        <div className="mt-3 p-3 rounded-xl bg-brand-500/10 border border-brand-500/20">
          <p className="text-xs text-brand-300 font-semibold mb-0.5">🎵 Pitch F0</p>
          <p className="text-xs text-white/50">
            f0_mean={summary[f0Idx] ? (
              intermediate.raw_features?.[119] != null
                ? `${Math.round(intermediate.raw_features[119])} Hz`
                : "—"
            ) : "—"},{" "}
            voiced_ratio={
              intermediate.raw_features?.[122] != null
                ? `${Math.round(intermediate.raw_features[122] * 100)}%`
                : "—"
            }
          </p>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Section 3: Similarity Histogram
// ─────────────────────────────────────────────
function SimilarityHistogram({ intermediate, topResult }) {
  const allSims = intermediate?.all_similarities ?? [];
  if (!allSims.length) return null;

  // Build 20 bins: 0–5%, 5–10%, ..., 95–100%
  const BINS = 20;
  const histData = Array.from({ length: BINS }, (_, i) => ({
    bin: `${i * 5}`,
    clarinet: 0,
    flute: 0,
    saxophone: 0,
    trumpet: 0,
  }));

  allSims.forEach(({ similarity, instrument }) => {
    const idx = Math.min(Math.floor(similarity * BINS), BINS - 1);
    if (histData[idx] && instrument in histData[idx]) {
      histData[idx][instrument]++;
    }
  });

  // Tìm bin của Top-1 để vẽ đường reference
  const top1Sim = topResult?.similarity ?? 0;
  const top1Bin = Math.min(Math.floor(top1Sim * BINS), BINS - 1);
  const top1BinLabel = histData[top1Bin]?.bin ?? "";

  return (
    <div className="glass rounded-2xl p-4 mb-4">
      <p className="text-xs text-white/40 uppercase tracking-widest mb-1">
        📈 Phân phối Cosine Similarity — toàn bộ {allSims.length} file trong DB
      </p>
      <p className="text-xs text-white/30 mb-4">
        Histogram tô màu theo nhạc cụ. Đường đứt nét trắng = điểm Top-1 (
        <span className="text-white/60 font-medium">
          {Math.round(top1Sim * 100)}%
        </span>
        ).
      </p>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={histData} margin={{ bottom: 30, right: 8 }}>
          <XAxis
            dataKey="bin"
            tick={{ fontSize: 9, fill: "#94a3b8" }}
            tickFormatter={(v) => `${v}%`}
            interval={1}
            angle={-35}
            textAnchor="end"
          />
          <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
          <Tooltip
            {...CHART_STYLE}
            labelFormatter={(label) => `Similarity ${label}–${Number(label) + 5}%`}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {["clarinet", "flute", "saxophone", "trumpet"].map((instr) => (
            <Bar
              key={instr}
              dataKey={instr}
              stackId="a"
              name={instr}
              fill={INST_COLORS[instr]}
            />
          ))}
          <ReferenceLine
            x={top1BinLabel}
            stroke="rgba(255,255,255,0.7)"
            strokeDasharray="4 3"
            strokeWidth={1.5}
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Legend tóm tắt per-instrument */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3">
        {["clarinet", "flute", "saxophone", "trumpet"].map((instr) => {
          const count = allSims.filter((s) => s.instrument === instr).length;
          return (
            <div key={instr} className="flex items-center gap-1.5">
              <span
                className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                style={{ background: INST_COLORS[instr] }}
              />
              <span className="text-xs text-white/50 capitalize">{instr}</span>
              <span className="text-xs text-white/30 ml-auto">{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Main export
// ─────────────────────────────────────────────
export default function IntermediateResults({ results }) {
  const intermediate = results?.intermediate;
  if (!intermediate) {
    return (
      <div className="glass rounded-2xl p-6 text-center text-white/30 text-sm">
        Không có dữ liệu trung gian.
      </div>
    );
  }

  return (
    <div>
      <WindowSection intermediate={intermediate} queryInfo={results?.query} />
      <FeatureSection intermediate={intermediate} />
      <SimilarityHistogram
        intermediate={intermediate}
        topResult={results?.results?.[0]}
      />
    </div>
  );
}
