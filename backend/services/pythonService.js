const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");

const PYTHON_SERVICE_URL =
  process.env.PYTHON_SERVICE_URL || "http://localhost:5001";

/**
 * Send an audio file to the Python service and get top-5 results.
 * @param {string} filePath - absolute path to the uploaded file
 * @param {string} originalName - original file name
 */
async function searchAudio(filePath, originalName) {
  const form = new FormData();
  form.append("file", fs.createReadStream(filePath), {
    filename: originalName,
    contentType: "application/octet-stream",
  });

  const response = await axios.post(`${PYTHON_SERVICE_URL}/search`, form, {
    headers: form.getHeaders(),
    timeout: 120000,
  });
  return response.data;
}

async function getStatus() {
  const response = await axios.get(`${PYTHON_SERVICE_URL}/status`, {
    timeout: 5000,
  });
  return response.data;
}

module.exports = { searchAudio, getStatus };
