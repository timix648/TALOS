"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface HealingRun {
  run_id: string;
  repo_full_name: string;
  status: string;
  error_type?: string;
  patient_zero?: string;
}

interface TalosAIChatProps {
  runs: HealingRun[];
  selectedRunId?: string;
}

export default function TalosAIChat({ runs, selectedRunId }: TalosAIChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [attachedRunId, setAttachedRunId] = useState<string | undefined>(selectedRunId);
  const [showRunPicker, setShowRunPicker] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

 
  useEffect(() => {
    if (selectedRunId) {
      setAttachedRunId(selectedRunId);
    }
  }, [selectedRunId]);

 
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          run_id: attachedRunId,
          history: messages.slice(-10), 
        }),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Chat failed: ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage: Message = { role: "assistant", content: data.response };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg = error instanceof DOMException && error.name === "AbortError"
        ? "Request timed out. The API may be unreachable. Please check your connection and try again."
        : "Sorry, I encountered an issue. Please try again in a moment.";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: errorMsg,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const attachRun = (runId: string) => {
    setAttachedRunId(runId);
    setShowRunPicker(false);
   
    const run = runs.find((r) => r.run_id === runId);
    if (run) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `I've attached the healing run for ${run.repo_full_name} (${run.status}). Feel free to ask me anything about this fix.`,
        },
      ]);
    }
  };

  const detachRun = () => {
    setAttachedRunId(undefined);
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: "Run detached. I'll answer general questions now. Attach a run to discuss a specific fix.",
      },
    ]);
  };

  const attachedRun = runs.find((r) => r.run_id === attachedRunId);

  return (
    <>
     
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed top-1/2 -translate-y-1/2 z-50 transition-all ${
          isOpen ? "right-[400px]" : "right-0"
        }`}
        whileHover={{ x: -4 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="bg-gradient-to-b from-cyan-500/90 to-purple-600/90 backdrop-blur-sm px-3 py-6 rounded-l-xl shadow-lg border-l border-t border-b border-cyan-400/30">
          {isOpen ? (
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          ) : (
            <div className="flex flex-col items-center gap-1">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <span className="text-[10px] text-white font-medium">AI</span>
            </div>
          )}
        </div>
      </motion.button>

   
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: 400 }}
            animate={{ x: 0 }}
            exit={{ x: 400 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 z-40 w-[400px] h-screen bg-gray-900 border-l border-gray-700/50 shadow-2xl flex flex-col"
          >
          
            <div className="bg-gradient-to-r from-gray-800/80 to-gray-900/80 border-b border-gray-700/50 p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-white font-semibold text-lg">TALOS AI</h3>
                  <p className="text-xs text-gray-400">Your healing assistant</p>
                </div>
                <button
                  onClick={() => setMessages([])}
                  className="text-gray-400 hover:text-gray-200 text-xs px-3 py-1.5 rounded-lg hover:bg-gray-700/50 transition-colors"
                >
                  Clear
                </button>
              </div>

            
              {attachedRun && (
                <div className="flex items-center gap-2 text-xs bg-gray-800/70 backdrop-blur-sm rounded-lg p-2.5 border border-gray-700/50">
                  <svg className="w-4 h-4 text-cyan-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                    />
                  </svg>
                  <span className="text-gray-300 truncate flex-1 font-medium">{attachedRun.repo_full_name}</span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      attachedRun.status === "completed"
                        ? "bg-green-100 text-green-700"
                        : attachedRun.status === "running"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {attachedRun.status}
                  </span>
                  <button onClick={detachRun} className="text-gray-400 hover:text-red-500 transition-colors">
                    ×
                  </button>
                </div>
              )}
            </div>

           
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-gray-900/50 to-gray-950">
              {messages.length === 0 && (
                <div className="text-center text-gray-400 mt-16">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center">
                    <svg className="w-8 h-8 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                      />
                    </svg>
                  </div>
                  <p className="text-sm font-medium text-gray-300">Ask me about TALOS fixes</p>
                  <p className="text-xs mt-2 text-gray-500">
                    {attachedRun
                      ? `Discussing: ${attachedRun.repo_full_name}`
                      : "Attach a run to discuss a specific fix"}
                  </p>
                </div>
              )}

              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                      msg.role === "user"
                        ? "bg-gradient-to-r from-cyan-500 to-purple-600 text-white rounded-br-sm shadow-sm"
                        : "bg-gray-800 text-gray-200 rounded-bl-sm border border-gray-700/50 shadow-sm"
                    }`}
                  >
                    <div className="text-sm leading-relaxed prose prose-sm prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-strong:text-cyan-300 prose-code:text-purple-300 prose-code:bg-gray-900/50 prose-code:px-1 prose-code:rounded">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-800 text-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 border border-gray-700/50 shadow-sm">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

           
            <AnimatePresence>
              {showRunPicker && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-gray-700/50 bg-gray-800 overflow-hidden"
                >
                  <div className="p-3 max-h-40 overflow-y-auto">
                    <p className="text-xs text-gray-400 mb-2 font-medium">Select a run to attach:</p>
                    <div className="space-y-1">
                      {runs.slice(0, 10).map((run) => (
                        <button
                          key={run.run_id}
                          onClick={() => attachRun(run.run_id)}
                          className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-700/50 transition-colors flex items-center justify-between border border-transparent hover:border-gray-600"
                        >
                          <span className="text-sm text-gray-300 truncate font-medium">{run.repo_full_name}</span>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                              run.status === "completed"
                                ? "bg-green-100 text-green-700"
                                : run.status === "running"
                                ? "bg-blue-100 text-blue-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {run.status}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            
            <div className="border-t border-gray-700/50 p-3 bg-gray-900">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowRunPicker(!showRunPicker)}
                  className={`p-2 rounded-lg transition-colors ${
                    showRunPicker ? "bg-cyan-500/20 text-cyan-400" : "text-gray-400 hover:text-cyan-400 hover:bg-gray-800"
                  }`}
                  title="Attach a healing run"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                    />
                  </svg>
                </button>
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about a fix..."
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 focus:bg-gray-800/80 transition-colors"
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || isLoading}
                  className="p-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-600 text-white hover:from-cyan-400 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
