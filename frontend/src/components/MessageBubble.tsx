import React from "react";
import { Bot, User, BookOpen } from "lucide-react";
import { ChatMessage } from "../types";
import { ToolCallBadge } from "./ToolCallBadge";

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === "user";

  // Lightweight markdown formatter for bolding, bullet points, and code blocks
  const renderFormattedContent = (content: string) => {
    const lines = content.split("\n");
    return lines.map((line, idx) => {
      // Bullet list items
      if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
        const text = line.trim().substring(2);
        return (
          <li key={idx} className="ml-4 list-disc text-slate-200 my-0.5">
            {formatInlineTokens(text)}
          </li>
        );
      }
      // Section headers
      if (line.trim().startsWith("### ")) {
        return (
          <h4 key={idx} className="font-bold text-slate-100 mt-2 mb-1 text-sm">
            {line.trim().substring(4)}
          </h4>
        );
      }
      if (line.trim().startsWith("## ")) {
        return (
          <h3 key={idx} className="font-bold text-indigo-300 mt-3 mb-1 text-base">
            {line.trim().substring(3)}
          </h3>
        );
      }
      if (line.trim() === "") {
        return <div key={idx} className="h-2" />;
      }
      return (
        <p key={idx} className="my-1 leading-relaxed">
          {formatInlineTokens(line)}
        </p>
      );
    });
  };

  const formatInlineTokens = (text: string) => {
    // Replace **bold** tokens
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-semibold text-white">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code key={i} className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 text-xs font-mono">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className={`flex gap-3 my-4 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center shrink-0 shadow-md shadow-indigo-500/20 text-white mt-1">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3.5 shadow-sm text-sm ${
          isUser
            ? "bg-indigo-600 text-white rounded-tr-none ml-12"
            : "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none mr-12"
        }`}
      >
        <div className="flex items-center justify-between gap-4 mb-1 text-[11px] opacity-75">
          <span className="font-medium">{isUser ? "You" : "Fintech Risk Advisor"}</span>
          <span>{message.timestamp}</span>
        </div>

        {/* Render tool execution badges if any */}
        {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
          <div className="mb-3 pt-1 border-b border-slate-800 pb-2">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
              <span>Deterministic Tools Executed ({message.tool_calls.length})</span>
            </div>
            <div className="flex flex-col gap-1">
              {message.tool_calls.map((tc, index) => (
                <ToolCallBadge key={index} toolCall={tc} />
              ))}
            </div>
          </div>
        )}

        {/* Message body */}
        <div className="space-y-1">{renderFormattedContent(message.content)}</div>

        {/* Sources citation footer */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center gap-2 text-xs text-slate-400">
            <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
            <span className="font-medium">Sources:</span>
            <div className="flex flex-wrap gap-1.5">
              {message.sources.map((src, idx) => (
                <span key={idx} className="bg-slate-800/80 px-2 py-0.5 rounded text-[11px] text-slate-300 font-mono">
                  {src}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 text-slate-300 mt-1">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
};
