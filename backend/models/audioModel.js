const mongoose = require("mongoose");

const audioSchema = new mongoose.Schema(
  {
    file_name: { type: String, required: true, unique: true },
    instrument: { type: String, required: true, index: true },
    duration: { type: Number },
    sample_rate: { type: Number },
    features: { type: [Number], required: true },
    file_path: { type: String },
  },
  { timestamps: true }
);

module.exports = mongoose.model("AudioFeature", audioSchema, "audio_features");
