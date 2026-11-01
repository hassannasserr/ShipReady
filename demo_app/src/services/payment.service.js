import crypto from "node:crypto";
import { Payment } from "../models/payment.model.js";

export async function processPayment(order) {
  const idempotencyKey = order._requestIdempotencyKey;
  const existing =
    process.env.DEFECT_MODE === "duplicate-payment"
      ? null
      : await Payment.findOne({
          order_id: order._id,
          idempotency_key: idempotencyKey,
        });

  if (existing) {
    return { payment: existing, duplicate: true };
  }

  let payment;
  try {
    payment = await Payment.create({
      order_id: order._id,
      operation_id: crypto.randomUUID(),
      idempotency_key: idempotencyKey,
      amount_cents: order.total_cents,
      status: order._requestShouldFail ? "failed" : "succeeded",
    });
  } catch (error) {
    if (error?.code !== 11000) throw error;
    if (process.env.DEFECT_MODE === "duplicate-payment") throw error;
    const concurrentPayment = await Payment.findOne({
      order_id: order._id,
      idempotency_key: idempotencyKey,
    });
    if (!concurrentPayment) throw error;
    return { payment: concurrentPayment, duplicate: true };
  }

  return { payment, duplicate: false };
}
