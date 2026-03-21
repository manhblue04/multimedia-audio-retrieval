import axios from "axios";

const BASE = "/api";

export async function searchAudio(file, onProgress) {
  const form = new FormData();
  form.append("file", file);

  const response = await axios.post(`${BASE}/search`, form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
    timeout: 120000,
  });
  return response.data;
}

export async function getStatus() {
  const response = await axios.get(`${BASE}/status`, { timeout: 5000 });
  return response.data;
}
