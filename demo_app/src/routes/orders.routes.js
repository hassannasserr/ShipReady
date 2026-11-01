import mongoose from "mongoose";
import { Order } from "../models/order.model.js";
import { Payment } from "../models/payment.model.js";
import { processPayment } from "../services/payment.service.js";

function invalidId(id) {
  return !mongoose.isValidObjectId(id);
}

function publicOrder(order, payments = []) {
  return {
    id: order._id.toString(),
    items: order.items,
    total_cents: order.total_cents,
    state: order.state,
    payments: payments.map((payment) => ({
      id: payment._id.toString(),
      operation_id: payment.operation_id,
      idempotency_key: payment.idempotency_key,
      amount_cents: payment.amount_cents,
      status: payment.status,
    })),
  };
}

function publicPayment(payment) {
  return {
    id: payment._id.toString(),
    operation_id: payment.operation_id,
    idempotency_key: payment.idempotency_key,
    amount_cents: payment.amount_cents,
    status: payment.status,
  };
}

export async function createOrder(request, response, next) {
  try {
    const items = request.body?.items;
    if (!Array.isArray(items) || items.length === 0) {
      return response.status(400).json({ error: "items must be a non-empty array." });
    }
    const total = items.reduce(
      (sum, item) => sum + item.quantity * item.unit_price_cents,
      0,
    );
    if (!Number.isInteger(total) || total <= 0) {
      return response.status(400).json({ error: "Items must have positive integer prices and quantities." });
    }
    const order = await Order.create({ items, total_cents: total });
    return response.status(201).json(publicOrder(order));
  } catch (error) {
    return next(error);
  }
}

export async function getOrder(request, response, next) {
  try {
    if (invalidId(request.params.orderId)) {
      return response.status(400).json({ error: "Invalid order ID." });
    }
    const order = await Order.findById(request.params.orderId);
    if (!order) {
      return response.status(404).json({ error: "Order not found." });
    }
    const payments = await Payment.find({ order_id: order._id }).sort({ createdAt: 1 });
    return response.json(publicOrder(order, payments));
  } catch (error) {
    return next(error);
  }
}

export async function payOrder(request, response, next) {
  try {
    if (invalidId(request.params.orderId)) {
      return response.status(400).json({ error: "Invalid order ID." });
    }
    const idempotencyKey = request.get("Idempotency-Key");
    if (!idempotencyKey || idempotencyKey.length > 128) {
      return response.status(400).json({ error: "A valid Idempotency-Key header is required." });
    }
    const order = await Order.findById(request.params.orderId);
    if (!order) {
      return response.status(404).json({ error: "Order not found." });
    }
    if (process.env.DEFECT_MODE !== "duplicate-payment") {
      const existing = await Payment.findOne({
        order_id: order._id,
        idempotency_key: idempotencyKey,
      });
      if (existing) {
        return response.status(200).json({
          payment: publicPayment(existing),
          order: { id: order._id.toString(), state: order.state },
          duplicate: true,
        });
      }
    }
    const allowsInvalidTransition =
      process.env.DEFECT_MODE === "invalid-transition" ||
      (process.env.DEFECT_MODE === "duplicate-payment" && order.state === "paid");
    if (order.state !== "pending" && !allowsInvalidTransition) {
      return response.status(409).json({ error: `Cannot pay an order in ${order.state} state.` });
    }

    order._requestIdempotencyKey = idempotencyKey;
    order._requestShouldFail = request.body?.simulate_failure === true;
    const { payment, duplicate } = await processPayment(order);
    if (!duplicate && payment.status === "succeeded") {
      order.state = "paid";
      await order.save();
    }
    return response.status(duplicate ? 200 : 201).json({
      payment: publicPayment(payment),
      order: { id: order._id.toString(), state: order.state },
      duplicate,
    });
  } catch (error) {
    return next(error);
  }
}

export async function cancelOrder(request, response, next) {
  try {
    if (invalidId(request.params.orderId)) {
      return response.status(400).json({ error: "Invalid order ID." });
    }
    const order = await Order.findById(request.params.orderId);
    if (!order) {
      return response.status(404).json({ error: "Order not found." });
    }
    if (order.state !== "pending") {
      return response.status(409).json({ error: `Cannot cancel an order in ${order.state} state.` });
    }
    order.state = "cancelled";
    await order.save();
    return response.json(publicOrder(order));
  } catch (error) {
    return next(error);
  }
}
