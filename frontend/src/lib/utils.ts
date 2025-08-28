import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
// src/lib/api.ts

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export async function chat(message: string, session_id: string) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Chat failed (${res.status}): ${text}`);
  }

  return res.json(); // { response: "..." }
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json(); // { status: "ok" }
}
