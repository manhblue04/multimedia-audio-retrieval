import { create } from "zustand";

const useSearchStore = create((set) => ({
  status: "idle", // idle | uploading | searching | done | error
  uploadProgress: 0,
  results: null,
  error: null,
  // Nhạc cụ thật do người dùng xác nhận (dùng tính Precision@5 client-side)
  groundTruth: "", // "" | "clarinet" | "flute" | "saxophone" | "trumpet"

  setStatus: (status) => set({ status }),
  setUploadProgress: (p) => set({ uploadProgress: p }),
  setResults: (results) => set({ results, status: "done", error: null }),
  setError: (error) => set({ error, status: "error" }),
  setGroundTruth: (gt) => set({ groundTruth: gt }),
  reset: () =>
    set({ status: "idle", uploadProgress: 0, results: null, error: null, groundTruth: "" }),
}));

export default useSearchStore;
