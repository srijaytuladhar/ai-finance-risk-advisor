import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Loader2, RefreshCw } from "lucide-react";
import { ChatMessage } from "../types";
import { sendChatMessage } from "../lib/api";
import { MessageBubble } from "./MessageBubble";

interface ChatWindowProps {
  onToolExecuted?: () => void;
}

const STARTER_PROMPTS = [
  "What is my total net worth and account balance breakdown?",
  "What are my top spending categories this year?",
  "How much did I spend on Eating Out, Chiya, and Groceries?",
  "What is my monthly cash flow and net savings rate?",
  "How much income did I receive from Fonepay salary and Side Hustles?",
  "Show me my expenses for the Manang trip and Bike servicing.",
];

export const ChatWindow: React.FC<ChatWindowProps> = ({ onToolExecuted }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome-1",
      role: "assistant",
      content:
        "Welcome to the **Fintech Financial & Ledger Risk Advisor**.\n\nI have loaded your complete personal financial records from `ledger.json` across **Citizen Bank**, **eSewa**, **Cash**, **Laxmi Bank**, and **Prabhu Bank** (1,433 transactions).\n\nEvery metric (account balances, category expenditures, cash flow, savings rate, and transaction search) is strictly computed via **deterministic financial tools** — zero numerical hallucinations.\n\nHow can I help you evaluate your accounts, spending, or cash flow today?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (userPrompt?: string) => {
    const textToSend = (userPrompt || input).trim();
    if (!textToSend || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Build history for conversational memory
      const historyPayload = messages
        .filter((m) => m.id !== "welcome-1")
        .slice(-6)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const res = await sendChatMessage({
        message: textToSend,
        history: historyPayload,
      });

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        tool_calls: res.tool_calls,
        sources: res.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      if (onToolExecuted && res.tool_calls && res.tool_calls.length > 0) {
        onToolExecuted();
      }
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `**Error:** ${err.message || "Failed to communicate with Risk Advisor agent."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: "assistant",
        content: "Conversation cleared. Feel free to ask a new risk question.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-full shadow-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white leading-tight">Risk Advisor Terminal</h2>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Hybrid Agent Online &bull; Deterministic Engine Active</span>
            </div>
          </div>
        </div>

        <button
          onClick={clearChat}
          className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors text-xs flex items-center gap-1 border border-slate-800"
          title="Reset conversation"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Reset</span>
        </button>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 p-5 overflow-y-auto space-y-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="flex items-center gap-3 text-slate-400 text-xs my-3 pl-2">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
            <span className="font-mono bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
              Synthesizing intent & executing deterministic quantitative tools...
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Starter Prompts */}
      <div className="px-5 py-2 border-t border-slate-800/80 bg-slate-950/40">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-amber-400" />
          Suggested Ledger Queries
        </div>
        <div className="flex flex-wrap gap-1.5">
          {STARTER_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              disabled={isLoading}
              className="text-xs bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white px-2.5 py-1 rounded-lg border border-slate-700/60 transition-all text-left truncate max-w-[280px]"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/90">
        <div className="flex items-end gap-2 bg-slate-950 border border-slate-800 rounded-xl p-2 focus-within:border-indigo-500/70 transition-all">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about accounts, spending, cash flow, trips (e.g., Manang), or salary..."
            rows={2}
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none px-2 py-1 leading-relaxed"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="p-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg transition-all shadow-md shadow-indigo-600/30 shrink-0"
            title="Send message (Enter)"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="flex justify-between items-center text-[10px] text-slate-400 mt-1.5 px-1">
          <span>Deterministic Ledger Policy: All balances, sums, & math computed via Python tools.</span>
          <span>Press Enter to send, Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );
};
