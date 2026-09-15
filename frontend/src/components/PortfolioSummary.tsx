import React, { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import {
  DollarSign,
  RefreshCw,
  Wallet,
  TrendingUp,
  PieChart as PieIcon,
  AlertCircle,
} from "lucide-react";
import { PortfolioData } from "../types";
import { fetchPortfolio } from "../lib/api";

const SECTOR_COLORS = [
  "#6366f1", // Indigo
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#06b6d4", // Cyan
  "#ec4899", // Pink
  "#8b5cf6", // Purple
  "#3b82f6", // Blue
  "#64748b", // Slate
];

export const PortfolioSummary: React.FC = () => {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const portfolio = await fetchPortfolio();
      setData(portfolio);
    } catch (err: any) {
      setError(err.message || "Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Format sector breakdown for Recharts
  const chartData = data?.sectors
    ? Object.entries(data.sectors).map(([sector, weight]) => ({
        name: sector,
        value: Math.round(weight * 1000) / 10, // e.g. 25.4%
      }))
    : [];

  const equityValue = data
    ? data.holdings.reduce((acc, h) => acc + h.value, 0)
    : 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Wallet className="w-5 h-5 text-indigo-400" />
            Portfolio Snapshot
          </h2>
          <p className="text-xs text-slate-400">Live holdings & risk exposures</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors border border-slate-800"
          title="Refresh Portfolio"
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

      {/* Metrics Row */}
      <div className="grid grid-cols-2 gap-3 my-4">
        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
            Total Equity + Cash
          </span>
          <div className="text-lg font-bold text-white mt-1">
            ${data?.total_value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "0.00"}
          </div>
          <div className="text-[11px] text-emerald-400 flex items-center gap-1 mt-0.5">
            <TrendingUp className="w-3 h-3" />
            Active Mandate
          </div>
        </div>

        <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
            Cash Reserves
          </span>
          <div className="text-lg font-bold text-emerald-400 mt-1">
            ${data?.cash.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "0.00"}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">
            {data && data.total_value > 0 ? `${((data.cash / data.total_value) * 100).toFixed(1)}% liquidity` : "0%"}
          </div>
        </div>
      </div>

      {/* Sector Allocation Pie Chart */}
      <div className="my-2 bg-slate-950/40 p-4 rounded-xl border border-slate-800/60">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <PieIcon className="w-4 h-4 text-indigo-400" />
            Sector Diversification
          </span>
          <span className="text-[10px] text-slate-400 font-mono">100% Target</span>
        </div>
        <div className="h-44 w-full">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={38}
                  outerRadius={65}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {chartData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={SECTOR_COLORS[index % SECTOR_COLORS.length]}
                      stroke="#0f172a"
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any) => [`${value}%`, "Weight"]}
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
              {loading ? "Loading allocations..." : "No sector data available"}
            </div>
          )}
        </div>

        {/* Custom Legend */}
        <div className="grid grid-cols-2 gap-1.5 mt-2">
          {chartData.map((entry, idx) => (
            <div key={idx} className="flex items-center gap-1.5 text-[11px] text-slate-300">
              <span
                className="w-2.5 h-2.5 rounded-sm shrink-0"
                style={{ backgroundColor: SECTOR_COLORS[idx % SECTOR_COLORS.length] }}
              />
              <span className="truncate">{entry.name}:</span>
              <span className="font-semibold ml-auto font-mono text-slate-200">{entry.value}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Holdings Table */}
      <div className="mt-3 flex-1 flex flex-col">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300">Current Positions</span>
          <span className="text-[11px] text-slate-400 font-mono">
            {data?.holdings.length || 0} Assets
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Ticker</th>
                <th className="py-2.5 px-3 text-right">Shares</th>
                <th className="py-2.5 px-3 text-right">Price</th>
                <th className="py-2.5 px-3 text-right">Value</th>
                <th className="py-2.5 px-3 text-right">Weight</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {data?.holdings.map((h, i) => (
                <tr key={i} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2 px-3 font-semibold text-white">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 border border-slate-700/60">
                      {h.ticker}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right text-slate-300">{h.shares}</td>
                  <td className="py-2 px-3 text-right text-slate-300">${h.price.toFixed(2)}</td>
                  <td className="py-2 px-3 text-right text-slate-200 font-medium">
                    ${h.value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-3 text-right text-indigo-400 font-semibold">
                    {(h.weight * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
