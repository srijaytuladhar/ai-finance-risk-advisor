import React, { useState } from "react";
import { Calculator, ChevronDown, ChevronRight, Database, Search, TrendingUp, CheckCircle2 } from "lucide-react";
import { ToolCallRecord } from "../types";

interface ToolCallBadgeProps {
  toolCall: ToolCallRecord;
}

export const ToolCallBadge: React.FC<ToolCallBadgeProps> = ({ toolCall }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getToolIcon = (name: string) => {
    if (name.includes("var") || name.includes("sharpe") || name.includes("volatility") || name.includes("beta")) {
      return <Calculator className="w-3.5 h-3.5 text-amber-400" />;
    }
    if (name.includes("search") || name.includes("doc")) {
      return <Search className="w-3.5 h-3.5 text-blue-400" />;
    }
    if (name.includes("price") || name.includes("history")) {
      return <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />;
    }
    return <Database className="w-3.5 h-3.5 text-indigo-400" />;
  };

  const formatArgs = (args: Record<string, any>) => {
    const keys = Object.keys(args);
    if (keys.length === 0) return "";
    return keys
      .slice(0, 2)
      .map((k) => `${k}=${JSON.stringify(args[k])}`)
      .join(", ") + (keys.length > 2 ? "..." : "");
  };

  return (
    <div className="my-1.5 inline-block w-full max-w-full">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg font-mono transition-all border text-left w-full sm:w-auto ${
          isExpanded
            ? "bg-slate-900 border-indigo-500/50 text-indigo-300 shadow-sm shadow-indigo-500/10"
            : "bg-slate-900/80 hover:bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700"
        }`}
        title="Click to view tool execution details"
      >
        <span className="flex items-center gap-1.5 font-medium">
          {getToolIcon(toolCall.name)}
          <span className="text-slate-200">{toolCall.name}</span>
        </span>

        {toolCall.args && Object.keys(toolCall.args).length > 0 && (
          <span className="text-slate-400 truncate max-w-[200px] text-[11px]">
            ({formatArgs(toolCall.args)})
          </span>
        )}

        <span className="ml-auto flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">
          <CheckCircle2 className="w-2.5 h-2.5" />
          deterministic
        </span>

        {isExpanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-2 p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono overflow-x-auto shadow-inner">
          <div className="text-[11px] text-slate-400 mb-1 font-semibold flex items-center justify-between">
            <span>Inputs:</span>
            <span className="text-[10px] text-slate-500">Method: {toolCall.result?.method || "standard"}</span>
          </div>
          <pre className="text-indigo-300 mb-2 whitespace-pre-wrap bg-slate-900/60 p-2 rounded border border-slate-800/50">
            {JSON.stringify(toolCall.args, null, 2)}
          </pre>

          <div className="text-[11px] text-slate-400 mb-1 font-semibold">Raw Tool Output:</div>
          <pre className="text-emerald-300 whitespace-pre-wrap bg-slate-900/60 p-2 rounded border border-slate-800/50 max-h-60 overflow-y-auto">
            {JSON.stringify(toolCall.result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
