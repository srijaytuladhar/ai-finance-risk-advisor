/**
 * Core type definitions for Fintech Financial & Ledger Risk Advisor.
 */

export interface Holding {
  ticker: string;
  shares: number;
  price: number;
  value: number;
  weight: number;
  sector?: string;
}

export interface AccountItem {
  id: string;
  name: string;
  type: string;
  balance: number;
  initial_balance: number;
  weight: number;
  color: string;
  is_default: boolean;
}

export interface CategorySummary {
  category: string;
  amount: number;
  percentage: number;
  count: number;
  color?: string;
  icon?: string;
}

export interface TransactionRecord {
  id: string;
  date: string;
  type: "Income" | "Expense" | "Transfer";
  amount: number;
  description: string;
  category: string;
  account_name: string;
}

export interface MonthlyCashflow {
  month: string;
  income: number;
  expense: number;
  net: number;
}

export interface PortfolioData {
  total_balance: number;
  total_income: number;
  total_expense: number;
  net_cashflow: number;
  savings_rate: number;
  transaction_count: number;
  accounts: AccountItem[];
  top_categories: CategorySummary[];
  monthly_cashflow: MonthlyCashflow[];
  recent_transactions: TransactionRecord[];

  // Compatibility fields
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
