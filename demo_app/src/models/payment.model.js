import mongoose from "mongoose";

const paymentSchema = new mongoose.Schema(
  {
    order_id: { type: mongoose.Schema.Types.ObjectId, ref: "Order", required: true },
    operation_id: { type: String, required: true, unique: true },
    idempotency_key: { type: String, required: true },
    amount_cents: { type: Number, required: true, min: 1 },
    status: { type: String, enum: ["succeeded", "failed"], required: true },
  },
  { timestamps: true, versionKey: false },
);

export const Payment = mongoose.model("Payment", paymentSchema);
