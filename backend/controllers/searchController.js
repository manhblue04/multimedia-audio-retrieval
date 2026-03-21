const fs = require("fs");
const path = require("path");
const pythonService = require("../services/pythonService");

/**
 * Build the URL to stream an audio file from the backend.
 * Serves via /audio/<instrument>/<filename>
 */
function buildAudioUrl(req, instrument, fileName) {
  const folder = instrument;
  const base = `${req.protocol}://${req.get("host")}`;
  return `${base}/audio/${folder}/${encodeURIComponent(fileName)}`;
}

exports.search = async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded" });
  }

  const filePath = req.file.path;
  try {
    const pyResult = await pythonService.searchAudio(filePath, req.file.originalname);

    // Enrich results with audio stream URLs
    const enrichedResults = (pyResult.results || []).map((item) => ({
      ...item,
      audio_url: buildAudioUrl(req, item.instrument, item.file_name),
    }));

    res.json({
      ...pyResult,
      results: enrichedResults,
    });
  } catch (err) {
    const message = err.response?.data?.error || err.message;
    res.status(500).json({ error: message });
  } finally {
    fs.unlink(filePath, () => {});
  }
};

exports.getStatus = async (req, res) => {
  try {
    const status = await pythonService.getStatus();
    res.json(status);
  } catch (err) {
    res.status(503).json({ error: "Python service unavailable", detail: err.message });
  }
};
