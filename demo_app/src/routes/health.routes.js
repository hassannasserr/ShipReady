import mongoose from "mongoose";

export function health(_request, response) {
  const healthy = mongoose.connection.readyState === 1;
  return response.status(healthy ? 200 : 503).json({
    status: healthy ? "healthy" : "unhealthy",
    database: healthy ? "connected" : "disconnected",
  });
}
