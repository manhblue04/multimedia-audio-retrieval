import { create } from "zustand";

const useSearchStore = create((set) => ({
  status: "idle", // idle | uploading | searching | done | error
  uploadProgress: 0,
  results: null,
  error: null,

  setStatus: (status) => set({ status }),
  setUploadProgress: (p) => set({ uploadProgress: p }),
  setResults: (results) => set({ results, status: "done", error: null }),
  setError: (error) => set({ error, status: "error" }),
  reset: () =>
    set({ status: "idle", uploadProgress: 0, results: null, error: null }),
}));

export default useSearchStore;
