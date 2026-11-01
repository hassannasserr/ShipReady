import mongoose from "mongoose";
import { createApp } from "./app.js";

const port = Number.parseInt(process.env.PORT ?? "3000", 10);
const mongoUri = process.env.MONGO_URI ?? "mongodb://localhost:27017/shipready_demo";
const app = createApp();

async function start() {
  await mongoose.connect(mongoUri, {
    serverSelectionTimeoutMS: 5000,
  });
  app.listen(port, "0.0.0.0", () => {
    console.log(`Demo Commerce API listening on port ${port}`);
  });
}

start().catch((error) => {
  console.error("Could not start Demo Commerce API:", error);
  process.exitCode = 1;
});

async function shutdown(signal) {
  console.log(`Received ${signal}; shutting down.`);
  await mongoose.disconnect();
  process.exit(0);
}

process.once("SIGTERM", () => shutdown("SIGTERM"));
process.once("SIGINT", () => shutdown("SIGINT"));
