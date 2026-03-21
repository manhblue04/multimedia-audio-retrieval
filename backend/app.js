require("dotenv").config();
const express = require("express");
const cors = require("cors");
const path = require("path");
const searchRoutes = require("./routes/searchRoutes");

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve dataset audio files so the frontend can play them
const DATASET_ROOT = path.resolve(
  process.env.DATASET_DIR || path.join(__dirname, "..", "dataset")
);
app.use("/audio", express.static(DATASET_ROOT));

// API routes
app.use("/api", searchRoutes);

app.get("/api/health", (req, res) => {
  res.json({ status: "ok", service: "backend" });
});

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});
