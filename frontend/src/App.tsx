import React, { useState, useEffect } from "react";
import { ShieldCheck, Activity, Layers, HelpCircle, Terminal } from "lucide-react";
import { ChatWindow } from "./components/ChatWindow";
import { PortfolioSummary } from "./components/PortfolioSummary";
import { checkBackendHealth } from "./lib/api";

export const App: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [modelName, setModelName] = useState<string>("gpt-4o-mini");
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  useEffect(() => {
    const verifyHealth = async () => {
      const res = await checkBackendHealth();
      if (res.status === "ok") {
        setBackendStatus("online");
        if (res.model) setModelName(res.model);
      } else {
        setBackendStatus("offline");
      }
    };
    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleToolExecuted = () => {
    // Increment trigger to signal children to refresh if needed
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-indigo-600/30">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base sm:text-lg font-bold tracking-tight text-white">
                  Fintech Portfolio Risk Advisor
                </h1>
                <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] uppercase font-mono font-semibold bg-indigo-950/80 border border-indigo-700/50 text-indigo-300">
                  v1.0 Production
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Hybrid LLM Reasoning &bull; Deterministic Tool Execution &bull; Zero Numerical Hallucinations
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* System Status Pill */}
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono">
              <span
                className={`w-2 h-2 rounded-full ${
                  backendStatus === "online"
                    ? "bg-emerald-400 animate-pulse"
                    : backendStatus === "checking"
                    ? "bg-amber-400"
                    : "bg-rose-500"
                }`}
              />
              <span className="text-slate-300 capitalize">
                {backendStatus === "online" ? "FastAPI Connected" : backendStatus}
              </span>
            </div>

            {/* Configured Model Badge */}
            <div className="hidden md:flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-300">
              <Terminal className="w-3.5 h-3.5 text-indigo-400" />
              <span>{modelName}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col lg:flex-row gap-6 h-[calc(100vh-4rem)]">
        {/* Left Column: Conversational AI Risk Terminal (60%) */}
        <div className="w-full lg:w-[60%] flex flex-col h-full min-h-[500px]">
          <ChatWindow onToolExecuted={handleToolExecuted} />
        </div>

        {/* Right Column: Portfolio Dashboard & Exposures (40%) */}
        <div className="w-full lg:w-[40%] flex flex-col h-full min-h-[500px]">
          <PortfolioSummary key={refreshTrigger} />
        </div>
      </main>
    </div>
  );
};

export default App;
