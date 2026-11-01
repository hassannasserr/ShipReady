import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { MongoMemoryServer } from "mongodb-memory-server";
import mongoose from "mongoose";
import request from "supertest";
import { createApp } from "../src/app.js";
import { Order } from "../src/models/order.model.js";
import { Payment } from "../src/models/payment.model.js";

let mongo;
let api;

before(async () => {
  mongo = await MongoMemoryServer.create();
  await mongoose.connect(mongo.getUri("shipready_test"));
  api = request(createApp());
});

after(async () => {
  await mongoose.disconnect();
  await mongo.stop();
});

async function createOrder() {
  const response = await api.post("/orders").send({
    items: [{ sku: "demo-widget", quantity: 2, unit_price_cents: 1250 }],
  });
  assert.equal(response.status, 201);
  return response.body.id;
}

test("health reports a connected database", async () => {
  const response = await api.get("/health");
  assert.equal(response.status, 200);
  assert.deepEqual(response.body, { status: "healthy", database: "connected" });
});

test("creates and retrieves a pending order", async () => {
  const orderId = await createOrder();
  const response = await api.get(`/orders/${orderId}`);
  assert.equal(response.status, 200);
  assert.equal(response.body.state, "pending");
  assert.equal(response.body.total_cents, 2500);
  assert.deepEqual(response.body.payments, []);
});

test("payment is idempotent for a repeated key", async () => {
  const orderId = await createOrder();
  const first = await api
    .post(`/orders/${orderId}/pay`)
    .set("Idempotency-Key", "payment-1");
  const second = await api
    .post(`/orders/${orderId}/pay`)
    .set("Idempotency-Key", "payment-1");

  assert.equal(first.status, 201);
  assert.equal(second.status, 200);
  assert.equal(second.body.duplicate, true);
  assert.equal(second.body.payment.operation_id, first.body.payment.operation_id);
  assert.equal(await Payment.countDocuments({ order_id: orderId }), 1);
  assert.equal((await Order.findById(orderId)).state, "paid");
});

test("rejects payment for a cancelled order without mutation", async () => {
  const orderId = await createOrder();
  const cancelled = await api.post(`/orders/${orderId}/cancel`);
  const payment = await api
    .post(`/orders/${orderId}/pay`)
    .set("Idempotency-Key", "payment-after-cancel");

  assert.equal(cancelled.status, 200);
  assert.equal(payment.status, 409);
  assert.equal(await Payment.countDocuments({ order_id: orderId }), 0);
  assert.equal((await Order.findById(orderId)).state, "cancelled");
});

test("defective variants are deterministic and isolated by environment", async () => {
  const orderId = await createOrder();
  const previous = process.env.DEFECT_MODE;
  process.env.DEFECT_MODE = "duplicate-payment";
  try {
    const first = await api
      .post(`/orders/${orderId}/pay`)
      .set("Idempotency-Key", "defect-key");
    const second = await api
      .post(`/orders/${orderId}/pay`)
      .set("Idempotency-Key", "defect-key");
    assert.equal(first.status, 201);
    assert.equal(second.status, 201);
    assert.equal(second.body.duplicate, false);
    assert.equal(await Payment.countDocuments({ order_id: orderId }), 2);
  } finally {
    if (previous === undefined) delete process.env.DEFECT_MODE;
    else process.env.DEFECT_MODE = previous;
  }
});

test("invalid-transition fixture permits payment after cancellation", async () => {
  const orderId = await createOrder();
  const cancelled = await api.post(`/orders/${orderId}/cancel`);
  assert.equal(cancelled.status, 200);
  const previous = process.env.DEFECT_MODE;
  process.env.DEFECT_MODE = "invalid-transition";
  try {
    const payment = await api
      .post(`/orders/${orderId}/pay`)
      .set("Idempotency-Key", "invalid-transition-key");
    assert.equal(payment.status, 201);
    assert.equal(payment.body.order.state, "paid");
  } finally {
    if (previous === undefined) delete process.env.DEFECT_MODE;
    else process.env.DEFECT_MODE = previous;
  }
});
