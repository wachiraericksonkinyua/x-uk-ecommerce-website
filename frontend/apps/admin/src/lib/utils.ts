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
  if (Array.isArray(product.product_images) && product.product_images.length > 0) {
    return product.product_images[0].image_url;
  }
  return product.image_url || "";
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

export const ORDER_STATUSES = [
  "Pending PIN",
  "Paid",
  "Processing",
  "Shipped",
  "Delivered",
  "Cancelled",
  "Payment Failed",
  "Refunded",
] as const;

export const LEAD_STATUSES = [
  "new",
  "warm",
  "hot",
  "cold",
  "won",
  "lost",
] as const;

export function statusColor(status?: string | null): string {
  switch (status) {
    case "Paid":
    case "Delivered":
    case "won":
      return "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/10";
    case "Processing":
    case "Shipped":
      return "bg-sky-50 text-sky-700 ring-1 ring-inset ring-sky-600/10";
    case "Refunded":
      return "bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-500/10";
    case "Cancelled":
    case "lost":
      return "bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-500/10";
    case "Payment Failed":
    case "hot":
      return "bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-600/10";
    case "warm":
      return "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/10";
    case "cold":
      return "bg-sky-50 text-sky-700 ring-1 ring-inset ring-sky-600/10";
    case "Pending PIN":
    case "new":
    default:
      return "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/10";
  }
}
