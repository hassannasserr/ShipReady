import mongoose from "mongoose";

export const ORDER_STATES = ["pending", "paid", "completed", "cancelled"];

const orderSchema = new mongoose.Schema(
  {
    items: {
      type: [
        {
          sku: { type: String, required: true, trim: true },
          quantity: { type: Number, required: true, min: 1 },
          unit_price_cents: { type: Number, required: true, min: 1 },
        },
      ],
      required: true,
      validate: {
        validator: (items) => items.length > 0,
        message: "At least one item is required.",
      },
    },
    total_cents: { type: Number, required: true, min: 1 },
    state: { type: String, enum: ORDER_STATES, default: "pending" },
  },
  { timestamps: true, versionKey: false },
);

export const Order = mongoose.model("Order", orderSchema);
