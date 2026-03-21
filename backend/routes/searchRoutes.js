const express = require("express");
const router = express.Router();
const multer = require("multer");
const path = require("path");
const searchController = require("../controllers/searchController");

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, path.join(__dirname, "..", "uploads"));
  },
  filename: (req, file, cb) => {
    const uniqueName = `${Date.now()}-${file.originalname}`;
    cb(null, uniqueName);
  },
});

const fileFilter = (req, file, cb) => {
  const allowed = /wav|mp3|ogg|flac|aiff|m4a/i;
  const ext = path.extname(file.originalname).slice(1);
  if (allowed.test(ext)) {
    cb(null, true);
  } else {
    cb(new Error(`Unsupported file type: ${ext}`), false);
  }
};

const upload = multer({ storage, fileFilter, limits: { fileSize: 50 * 1024 * 1024 } });

router.post("/search", upload.single("file"), searchController.search);
router.get("/status", searchController.getStatus);

module.exports = router;
