import clsx, { type ClassValue } from "clsx";
import type { Product } from "./types";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatKES(amount: number | string | null | undefined): string {
  const value = typeof amount === "string" ? Number(amount) : amount ?? 0;
  const safe = Number.isFinite(value) ? (value as number) : 0;
  return `KES ${safe.toLocaleString("en-KE", { maximumFractionDigits: 0 })}`;
}

export function productImage(product?: Partial<Product> | null): string {
  if (!product) return "";
  return product.image_url || product.product_images?.[0]?.image_url || "";
}

export function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-KE", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const ORDER_STATUS_STEPS = [
  { key: "placed", label: "Order Placed / Paid" },
  { key: "dispatch", label: "Fulfillment & Dispatch" },
  { key: "completed", label: "Completed" },
] as const;

export function orderStepIndex(status?: string | null): number {
  switch (status) {
    case "Delivered":
      return 2;
    case "Processing":
    case "Shipped":
      return 1;
    case "Pending PIN":
    case "Paid":
    default:
      return 0;
  }
}

export function statusColor(status?: string | null): string {
  switch (status) {
    case "Paid":
      return "bg-emerald-100 text-emerald-700";
    case "Processing":
      return "bg-blue-100 text-blue-700";
    case "Shipped":
      return "bg-indigo-100 text-indigo-700";
    case "Delivered":
      return "bg-emerald-100 text-emerald-700";
    case "Cancelled":
      return "bg-slate-200 text-slate-600";
    case "Payment Failed":
      return "bg-rose-100 text-rose-700";
    case "Pending PIN":
    default:
      return "bg-amber-100 text-amber-700";
  }
}
