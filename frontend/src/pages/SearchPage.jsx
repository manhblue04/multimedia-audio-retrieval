import { useEffect, useRef, useState } from "react";
import AudioUploader from "../components/AudioUploader";
import ResultList from "../components/ResultList";
import AudioPlayer from "../components/AudioPlayer";
import useSearchStore from "../store/searchStore";
import { searchAudio, getStatus } from "../services/api";

function StatCard({ label, value, sub, color = "text-brand-400" }) {
  return (
    <div className="glass rounded-xl p-4 text-center">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-white/50 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-white/30 mt-0.5">{sub}</p>}
    </div>
  );
}

function UploadingIndicator({ progress }) {
  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 animate-spin" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(66,153,225,0.15)" strokeWidth="6" />
          <circle
            cx="40" cy="40" r="36" fill="none"
            stroke="#4299e1" strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 36 * progress / 100} ${2 * Math.PI * 36}`}
            transform="rotate(-90 40 40)"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-brand-400">
          {progress}%
        </span>
      </div>
      <p className="text-white/60 text-sm">Đang tải file lên...</p>
    </div>
  );
}

function SearchingIndicator() {
  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <div className="relative w-20 h-20">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute inset-0 rounded-full border-2 border-brand-500/60 animate-ping"
            style={{ animationDelay: `${i * 0.3}s`, animationDuration: "1.5s" }}
          />
        ))}
        <div className="absolute inset-0 flex items-center justify-center">
          <svg className="w-8 h-8 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>
      <p className="text-white/60 text-sm">Đang phân tích và tìm kiếm...</p>
    </div>
  );
}

export default function SearchPage() {
  const { status, uploadProgress, results, error, setStatus, setUploadProgress, setResults, setError, reset } =
    useSearchStore();

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dbStatus, setDbStatus] = useState(null);

  useEffect(() => {
    getStatus()
      .then(setDbStatus)
      .catch(() => setDbStatus(null));
  }, []);

  const handleFile = (file) => {
    reset();
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleSearch = async () => {
    if (!selectedFile) return;
    setStatus("uploading");
    setUploadProgress(0);
    try {
      const data = await searchAudio(selectedFile, (p) => {
        setUploadProgress(p);
        if (p >= 100) setStatus("searching");
      });
      setResults(data);
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Lỗi không xác định");
    }
  };

  const handleReset = () => {
    reset();
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
  };

  const isLoading = status === "uploading" || status === "searching";
  const isDone = status === "done";
  const hasError = status === "error";

  return (
    <div className="min-h-screen bg-dark-950 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-brand-600/10 blur-3xl" />
        <div className="absolute top-1/2 -right-40 w-80 h-80 rounded-full bg-purple-600/8 blur-3xl" />
        <div className="absolute -bottom-20 left-1/3 w-72 h-72 rounded-full bg-brand-500/8 blur-3xl" />
      </div>

      <div className="relative z-10 max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <span className="text-xs font-semibold text-brand-400 uppercase tracking-widest">
              Wind Instrument Finder
            </span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">
            Tìm kiếm nhạc cụ hơi
          </h1>
          <p className="text-white/40 text-sm max-w-md mx-auto">
            Upload file âm thanh — hệ thống sẽ tìm 5 bản ghi tương đồng nhất
            từ tập dữ liệu sử dụng đặc trưng MFCC + Cosine Similarity
          </p>
        </div>

        {/* DB Status bar */}
        {dbStatus && (
          <div className="flex items-center justify-center gap-4 mb-8 text-xs text-white/40">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
              {dbStatus.total_documents?.toLocaleString()} file trong DB
            </span>
            {dbStatus.instruments?.map((i) => (
              <span key={i} className="capitalize">{i}</span>
            ))}
          </div>
        )}

        {/* Main card */}
        <div className="glass rounded-3xl p-6 md:p-8 glow mb-6">
          {/* Upload zone */}
          {!isLoading && !isDone && (
            <AudioUploader onFile={handleFile} disabled={isLoading} />
          )}

          {/* Selected file preview */}
          {selectedFile && !isLoading && !isDone && (
            <div className="mt-6 p-4 glass rounded-2xl">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{selectedFile.name}</p>
                  <p className="text-xs text-white/40">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  onClick={handleReset}
                  className="text-white/30 hover:text-white/70 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              {previewUrl && <AudioPlayer audioUrl={previewUrl} label="Xem trước file upload" />}
            </div>
          )}

          {/* Loading states */}
          {status === "uploading" && <UploadingIndicator progress={uploadProgress} />}
          {status === "searching" && <SearchingIndicator />}

          {/* Error */}
          {hasError && (
            <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
              <p className="font-semibold mb-1">Lỗi tìm kiếm</p>
              <p className="text-red-400/80 text-xs">{error}</p>
              <button onClick={handleReset} className="mt-3 text-xs text-red-300 underline">
                Thử lại
              </button>
            </div>
          )}

          {/* Search button */}
          {selectedFile && !isLoading && !isDone && (
            <button
              onClick={handleSearch}
              className="mt-6 w-full py-3.5 rounded-2xl bg-brand-500 hover:bg-brand-400 active:scale-95
                transition-all font-semibold text-white text-sm glow flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Tìm kiếm
            </button>
          )}

          {/* Reset when done */}
          {isDone && (
            <button
              onClick={handleReset}
              className="w-full py-3 rounded-2xl border border-white/10 text-white/60
                hover:text-white hover:border-white/30 transition-all text-sm flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Tìm kiếm mới
            </button>
          )}
        </div>

        {/* Stats cards when done */}
        {isDone && results && (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
              <StatCard
                label="Thời gian tìm kiếm"
                value={`${results.search_time_ms}ms`}
                color="text-brand-400"
              />
              <StatCard
                label="Nhạc cụ dự đoán"
                value={results.predicted_instrument || "—"}
                color="text-green-400"
              />
              <StatCard
                label="Độ tin cậy (SVM)"
                value={`${Math.round((results.confidence || 0) * 100)}%`}
                color="text-amber-400"
              />
              <StatCard
                label="Precision@5"
                value={`${Math.round((results.precision_at_5 || 0) * 100)}%`}
                color="text-purple-400"
              />
            </div>
            {/* SVM probability breakdown */}
            {results.probabilities && Object.keys(results.probabilities).length > 0 && (
              <div className="glass rounded-2xl p-4 mb-4">
                <p className="text-xs text-white/40 uppercase tracking-widest mb-3">Xác suất từng nhạc cụ (SVM)</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {Object.entries(results.probabilities)
                    .sort((a, b) => b[1] - a[1])
                    .map(([instr, prob]) => {
                      const pct = Math.round(prob * 100);
                      const isTop = instr === results.predicted_instrument;
                      return (
                        <div key={instr} className={`rounded-xl p-3 ${isTop ? "bg-green-500/15 border border-green-500/30" : "bg-white/5"}`}>
                          <div className="flex justify-between items-center mb-1">
                            <span className={`text-xs font-medium capitalize ${isTop ? "text-green-300" : "text-white/60"}`}>{instr}</span>
                            <span className={`text-xs font-bold ${isTop ? "text-green-400" : "text-white/40"}`}>{pct}%</span>
                          </div>
                          <div className="h-1 rounded-full bg-white/10 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${isTop ? "bg-green-400" : "bg-white/20"}`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}
          </>
        )}

        {/* Results */}
        {isDone && results?.results && <ResultList results={results.results} />}

        {/* Footer info */}
        <p className="text-center text-xs text-white/20 mt-10">
          MFCC · Spectral Centroid · Bandwidth · RMS · ZCR · Spectral Contrast · Cosine Similarity
        </p>
      </div>
    </div>
  );
}
