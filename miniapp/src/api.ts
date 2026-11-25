const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type Theme = {
  id: string;
  title_ru: string;
  learning_goal: string;
  age_range: string;
};

export type Style = { id: string; title_ru: string };

export type OrderStatus =
  | "pending"
  | "generating_text"
  | "generating_images"
  | "building_pdf"
  | "done"
  | "failed";

export type Order = {
  id: string;
  status: OrderStatus;
  progress_percent: number;
  page_count?: number;
  preview_urls?: string[];
  pdf_url?: string;
  error_message?: string;
};

export async function fetchThemes(): Promise<Theme[]> {
  const r = await fetch(`${API}/api/themes`);
  if (!r.ok) throw new Error("themes");
  return r.json();
}

export async function fetchStyles(): Promise<Style[]> {
  const r = await fetch(`${API}/api/styles`);
  if (!r.ok) throw new Error("styles");
  return r.json();
}

export async function createOrder(form: FormData): Promise<{ id: string; status: OrderStatus }> {
  const r = await fetch(`${API}/api/orders`, { method: "POST", body: form });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail || "order_failed");
  }
  return r.json();
}

export async function getOrder(id: string, initData: string): Promise<Order> {
  const q = new URLSearchParams({ init_data: initData });
  const r = await fetch(`${API}/api/orders/${id}?${q}`);
  if (!r.ok) throw new Error("order_status");
  return r.json();
}