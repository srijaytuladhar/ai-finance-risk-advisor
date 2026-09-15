/**
 * API client library for connecting to the FastAPI backend.
 */

import { ChatRequest, ChatResponse, PortfolioData } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Fetch the latest portfolio snapshot, including live holdings, valuations, and sectors.
 */
export async function fetchPortfolio(): Promise<PortfolioData> {
  const res = await fetch(`${API_BASE_URL}/api/portfolio`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Failed to fetch portfolio: ${res.status} ${res.statusText} - ${errorBody}`);
  }

  return res.json();
}

/**
 * Send a chat query to the LangGraph agent and receive response with tool call records.
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Chat API error: ${res.status} ${res.statusText} - ${errorBody}`);
  }

  return res.json();
}

/**
 * Check backend service health status.
 */
export async function checkBackendHealth(): Promise<{ status: string; service?: string; model?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, { method: "GET" });
    if (!res.ok) return { status: "error" };
    return res.json();
  } catch {
    return { status: "offline" };
  }
}
