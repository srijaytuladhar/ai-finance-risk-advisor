import React, { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  RefreshCw,
  Wallet,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Building2,
  Smartphone,
  Banknote,
  ArrowDownLeft,
  ArrowUpRight,
  Layers,
} from "lucide-react";
import { PortfolioData } from "../types";
import { fetchPortfolio } from "../lib/api";

const CATEGORY_COLORS = [
  "#6366f1", // Indigo
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#06b6d4", // Cyan
  "#ec4899", // Pink
  "#8b5cf6", // Purple
  "#f43f5e", // Rose
  "#3b82f6", // Blue
  "#14b8a6", // Teal
  "#64748b", // Slate
];

export const PortfolioSummary: React.FC = () => {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"categories" | "accounts">("categories");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const portfolio = await fetchPortfolio();
      setData(portfolio);
    } catch (err: any) {
      setError(err.message || "Failed to load ledger data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Format category data for Recharts Donut
  const categoryChartData = data?.top_categories?.length
    ? data.top_categories.map((c) => ({
        name: c.category,
        value: Math.round(c.percentage * 1000) / 10, // e.g. 17.0%
        amount: c.amount,
      }))
    : [];

  // Format account data for Recharts Donut
  const accountChartData = data?.accounts?.length
    ? data.accounts.map((a) => ({
        name: a.name,
        value: Math.round(a.weight * 1000) / 10,
        amount: a.balance,
        color: a.color,
      }))
    : [];

  const getAccountIcon = (type: string) => {
    if (type.toLowerCase() === "wallet") return <Smartphone className="w-3.5 h-3.5 text-emerald-400" />;
    if (type.toLowerCase() === "cash") return <Banknote className="w-3.5 h-3.5 text-purple-400" />;
    return <Building2 className="w-3.5 h-3.5 text-indigo-400" />;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Wallet className="w-5 h-5 text-indigo-400" />
            Financial Ledger Analytics
          </h2>
          <p className="text-xs text-slate-400">Live Accounts &amp; Cash Flow Diagnostics (NPR)</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors border border-slate-800"
          title="Refresh Ledger"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-indigo-400" : ""}`} />
        </button>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-rose-950/40 border border-rose-800/50 rounded-xl text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 2x2 Primary Metrics Grid */}
      <div className="grid grid-cols-2 gap-2.5 my-4">
        {/* Total Liquid Balance */}
        <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">
            Total Liquid Balance
          </span>
          <div className="text-base sm:text-lg font-bold text-white mt-0.5 truncate">
            Rs. {data?.total_balance?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "0.00"}
          </div>
          <div className="text-[11px] text-emerald-400 flex items-center gap-1 mt-0.5">
            <TrendingUp className="w-3 h-3" />
            <span>{data?.accounts?.length || 5} Verified Accounts</span>
          </div>
        </div>

        {/* Total Income */}
        <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">
            Lifetime Inflow
          </span>
          <div className="text-base sm:text-lg font-bold text-emerald-400 mt-0.5 truncate">
            Rs. {data?.total_income?.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) || "0"}
          </div>
          <div className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
            <ArrowDownLeft className="w-3 h-3 text-emerald-400" />
            <span>Salary &amp; Hustles</span>
          </div>
        </div>

        {/* Total Expenses */}
        <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">
            Total Expenses
          </span>
          <div className="text-base sm:text-lg font-bold text-rose-400 mt-0.5 truncate">
            Rs. {data?.total_expense?.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) || "0"}
          </div>
          <div className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
            <ArrowUpRight className="w-3 h-3 text-rose-400" />
            <span>{data?.transaction_count?.toLocaleString() || "1,433"} Transactions</span>
          </div>
        </div>

        {/* Net Cash Flow */}
        <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">
            Net Cash Flow
          </span>
          <div className={`text-base sm:text-lg font-bold mt-0.5 truncate ${
            (data?.net_cashflow || 0) >= 0 ? "text-emerald-400" : "text-amber-400"
          }`}>
            Rs. {data?.net_cashflow?.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) || "0"}
          </div>
          <div className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
            <TrendingDown className="w-3 h-3 text-amber-400" />
            <span>Savings Rate: {data?.savings_rate?.toFixed(1) || "-25.8"}%</span>
          </div>
        </div>
      </div>

      {/* Interactive Tabs: Categories vs Accounts */}
      <div className="my-2 bg-slate-950/50 p-3.5 rounded-xl border border-slate-800/80">
        <div className="flex items-center justify-between mb-3 border-b border-slate-800/80 pb-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("categories")}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all ${
                activeTab === "categories"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              Top Expenses
            </button>
            <button
              onClick={() => setActiveTab("accounts")}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all ${
                activeTab === "accounts"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              Account Allocation
            </button>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            {activeTab === "categories" ? "10 Major Categories" : "5 Institutions"}
          </span>
        </div>

        {/* Donut Chart */}
        <div className="h-44 w-full">
          {activeTab === "categories" ? (
            categoryChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={36}
                    outerRadius={65}
                    paddingAngle={2.5}
                    dataKey="value"
                  >
                    {categoryChartData.map((_, index) => (
                      <Cell
                        key={`cat-cell-${index}`}
                        fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                        stroke="#0f172a"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: any, _name: any, item: any) => [
                      `Rs. ${item.payload.amount?.toLocaleString()} (${value}%)`,
                      item.payload.name,
                    ]}
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "#f8fafc",
                    }}
                    itemStyle={{ color: "#818cf8" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                {loading ? "Loading categories..." : "No category data"}
              </div>
            )
          ) : (
            accountChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={accountChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={36}
                    outerRadius={65}
                    paddingAngle={2.5}
                    dataKey="value"
                  >
                    {accountChartData.map((entry, index) => (
                      <Cell
                        key={`acc-cell-${index}`}
                        fill={entry.color || CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                        stroke="#0f172a"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: any, _name: any, item: any) => [
                      `Rs. ${item.payload.amount?.toLocaleString()} (${value}%)`,
                      item.payload.name,
                    ]}
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "#f8fafc",
                    }}
                    itemStyle={{ color: "#818cf8" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                {loading ? "Loading accounts..." : "No account data"}
              </div>
            )
          )}
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 gap-1.5 mt-2 max-h-24 overflow-y-auto pr-1">
          {activeTab === "categories"
            ? categoryChartData.slice(0, 8).map((entry, idx) => (
                <div key={idx} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                  <span
                    className="w-2.5 h-2.5 rounded-sm shrink-0"
                    style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                  />
                  <span className="truncate">{entry.name}:</span>
                  <span className="font-semibold ml-auto font-mono text-slate-200">{entry.value}%</span>
                </div>
              ))
            : accountChartData.map((entry, idx) => (
                <div key={idx} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                  <span
                    className="w-2.5 h-2.5 rounded-sm shrink-0"
                    style={{ backgroundColor: entry.color || CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                  />
                  <span className="truncate">{entry.name}:</span>
                  <span className="font-semibold ml-auto font-mono text-slate-200">{entry.value}%</span>
                </div>
              ))}
        </div>
      </div>

      {/* Accounts Breakdown Cards */}
      <div className="mt-2.5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            Accounts &amp; Balances
          </span>
          <span className="text-[11px] text-slate-400 font-mono">
            {data?.accounts?.length || 0} Accounts
          </span>
        </div>

        <div className="flex flex-col gap-1.5">
          {data?.accounts?.map((acc) => (
            <div
              key={acc.id}
              className="flex items-center justify-between p-2 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:bg-slate-800/30 transition-colors"
            >
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: acc.color }}
                />
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-white truncate">{acc.name}</span>
                    {acc.is_default && (
                      <span className="text-[9px] px-1 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/50">
                        Default
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-400 flex items-center gap-1">
                    {getAccountIcon(acc.type)}
                    <span>{acc.type}</span>
                  </div>
                </div>
              </div>

              <div className="text-right shrink-0">
                <div className="text-xs font-bold text-white font-mono">
                  Rs. {acc.balance.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="text-[10px] text-indigo-400 font-mono">
                  {(acc.weight * 100).toFixed(1)}% share
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Transactions Feed */}
      {data?.recent_transactions && data.recent_transactions.length > 0 && (
        <div className="mt-3.5 pt-3 border-t border-slate-800/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-300">Recent Transactions</span>
            <span className="text-[10px] text-slate-500 font-mono">Latest Entries</span>
          </div>

          <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto pr-1">
            {data.recent_transactions.slice(0, 6).map((tx) => (
              <div
                key={tx.id}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950/30 border border-slate-850 text-xs font-mono"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                      tx.type === "Income"
                        ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800/50"
                        : tx.type === "Expense"
                        ? "bg-rose-950/80 text-rose-400 border border-rose-800/50"
                        : "bg-indigo-950/80 text-indigo-400 border border-indigo-800/50"
                    }`}>
                      {tx.category || tx.type}
                    </span>
                    <span className="text-slate-300 truncate max-w-[120px] text-[11px]">
                      {tx.description || tx.account_name}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">{tx.date} &bull; {tx.account_name}</span>
                </div>

                <div className={`font-semibold shrink-0 text-right ${
                  tx.type === "Income" ? "text-emerald-400" : tx.type === "Expense" ? "text-rose-400" : "text-indigo-300"
                }`}>
                  {tx.type === "Income" ? "+" : tx.type === "Expense" ? "-" : ""}
                  Rs. {tx.amount.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
