/**
 * Core type definitions for Fintech Portfolio Risk Advisor.
 */

export interface Holding {
  ticker: string;
  shares: number;
  price: number;
  value: number;
  weight: number;
  sector?: string;
}

export interface PortfolioData {
  holdings: Holding[];
  cash: number;
  total_value: number;
  weights: Record<string, number>;
  sectors: Record<string, number>;
}

export interface ToolCallRecord {
  name: string;
  args: Record<string, any>;
  result: any;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  tool_calls?: ToolCallRecord[];
  sources?: string[];
}

export interface ChatRequest {
  message: string;
  history: Array<{ role: string; content: string }>;
}

export interface ChatResponse {
  response: string;
  tool_calls: ToolCallRecord[];
  sources: string[];
}
