import express from "express";
import { createOrder, getOrder, payOrder, cancelOrder } from "./routes/orders.routes.js";
import { health } from "./routes/health.routes.js";

export function createApp() {
  const app = express();
  app.use(express.json({ limit: "32kb" }));
  app.use(async (request, _response, next) => {
    const delay = Number.parseInt(process.env.DEMO_DELAY_MS ?? "0", 10);
    if (delay > 0 && request.path !== "/health") {
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
    next();
  });

  app.get("/health", health);
  app.post("/orders", createOrder);
  app.get("/orders/:orderId", getOrder);
  app.post("/orders/:orderId/pay", payOrder);
  app.post("/orders/:orderId/cancel", cancelOrder);

  app.use((error, _request, response, _next) => {
    if (error instanceof SyntaxError && "body" in error) {
      return response.status(400).json({ error: "Request body must be valid JSON." });
    }
    console.error(error);
    return response.status(500).json({ error: "Internal server error." });
  });

  return app;
}
