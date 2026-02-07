"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import {
  Rocket,
  Flag,
  GitBranch,
  Search,
  FileCode,
  Brain,
  Microscope,
  Stethoscope,
  Wrench,
  TestTube,
  GitPullRequest,
  CheckCircle2,
  XCircle,
  RefreshCw,
  FileDiff,
  AlertCircle,
  Sparkles,
  Loader2,
  Link as LinkIcon,
  Dna,
  Camera,
  Eye,
} from "lucide-react";

const EVENT_CONFIG: Record<string, { bg: string; border: string; text: string; dot: string; icon: React.ElementType }> = {
  mission_start: { bg: "bg-blue-500/10", border: "border-blue-500/30", text: "text-blue-400", dot: "bg-blue-500", icon: Rocket },
  mission_end: { bg: "bg-purple-500/10", border: "border-purple-500/30", text: "text-purple-400", dot: "bg-purple-500", icon: Flag },
  cloning: { bg: "bg-yellow-500/10", border: "border-yellow-500/30", text: "text-yellow-400", dot: "bg-yellow-500", icon: GitBranch },
  scouting: { bg: "bg-yellow-500/10", border: "border-yellow-500/30", text: "text-yellow-400", dot: "bg-yellow-500", icon: Search },
  reading_code: { bg: "bg-yellow-500/10", border: "border-yellow-500/30", text: "text-yellow-400", dot: "bg-yellow-500", icon: FileCode },
  thinking: { bg: "bg-cyan-500/10", border: "border-cyan-500/30", text: "text-cyan-400", dot: "bg-cyan-500", icon: Brain },
  analyzing: { bg: "bg-cyan-500/10", border: "border-cyan-500/30", text: "text-cyan-400", dot: "bg-cyan-500", icon: Microscope },
  diagnosing: { bg: "bg-cyan-500/10", border: "border-cyan-500/30", text: "text-cyan-400", dot: "bg-cyan-500", icon: Stethoscope },
  applying_fix: { bg: "bg-green-500/10", border: "border-green-500/30", text: "text-green-400", dot: "bg-green-500", icon: Wrench },
  verifying: { bg: "bg-green-500/10", border: "border-green-500/30", text: "text-green-400", dot: "bg-green-500", icon: TestTube },
  creating_pr: { bg: "bg-green-500/10", border: "border-green-500/30", text: "text-green-400", dot: "bg-green-500", icon: GitPullRequest },
  success: { bg: "bg-green-500/10", border: "border-green-500/30", text: "text-green-400", dot: "bg-green-500", icon: CheckCircle2 },
  failure: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400", dot: "bg-red-500", icon: XCircle },
  retry: { bg: "bg-orange-500/10", border: "border-orange-500/30", text: "text-orange-400", dot: "bg-orange-500", icon: RefreshCw },
  code_diff: { bg: "bg-pink-500/10", border: "border-pink-500/30", text: "text-pink-400", dot: "bg-pink-500", icon: FileDiff },
  error_log: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400", dot: "bg-red-500", icon: AlertCircle },
  thought_stream: { bg: "bg-purple-500/10", border: "border-purple-500/30", text: "text-purple-400", dot: "bg-purple-500", icon: Sparkles },
  screenshot: { bg: "bg-indigo-500/10", border: "border-indigo-500/30", text: "text-indigo-400", dot: "bg-indigo-500", icon: Camera },
  visual_analysis: { bg: "bg-violet-500/10", border: "border-violet-500/30", text: "text-violet-400", dot: "bg-violet-500", icon: Eye },
};

const DEFAULT_CONFIG = { bg: "bg-gray-500/10", border: "border-gray-500/30", text: "text-gray-400", dot: "bg-gray-500", icon: Dna };

export interface TimelineEvent {
  run_id: string;
  event_type: string;
  title: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

interface TimelineProps {
  runId: string;
  apiBaseUrl?: string;
  onComplete?: (status: "success" | "failure") => void;
}

function TimelineEventCard({ event, isLatest }: { event: TimelineEvent; isLatest: boolean }) {
  const config = EVENT_CONFIG[event.event_type] || DEFAULT_CONFIG;
  const [isExpanded, setIsExpanded] = useState(false);
  const Icon = config.icon;

  const time = new Date(event.timestamp).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const hasMetadata = Boolean(event.metadata && Object.keys(event.metadata).length > 0);
  const showExpandedMetadata = isExpanded && hasMetadata;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -20, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.3 }}
      className="relative pl-6 sm:pl-8"
    >
      <div className="absolute left-[9px] sm:left-[11px] top-6 bottom-0 w-0.5 bg-gradient-to-b from-gray-700 to-transparent" />

      <motion.div
        className={`absolute left-0 top-2 w-5 h-5 sm:w-6 sm:h-6 rounded-full ${config.dot} flex items-center justify-center`}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
      >
        {isLatest && (
          <motion.div
            className={`absolute inset-0 rounded-full ${config.dot}`}
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}
        <Icon className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-white" />
      </motion.div>

      <motion.div
        className={`${config.bg} ${config.border} border rounded-xl p-3 sm:p-4 mb-3 sm:mb-4 cursor-pointer hover:border-opacity-60 transition-all`}
        onClick={() => setIsExpanded(!isExpanded)}
        whileHover={{ scale: 1.01 }}
      >
        <div className="flex items-start justify-between gap-2 sm:gap-4">
          <div className="flex-1 min-w-0">
            <h3 className={`font-semibold text-sm sm:text-base ${config.text} truncate flex items-center gap-2`}>
              <Icon className={`w-4 h-4 flex-shrink-0 ${config.text}`} />
              {event.title}
            </h3>
            <p className="text-gray-400 text-xs sm:text-sm mt-1 line-clamp-2">
              {event.description}
            </p>
          </div>
          <span className="text-gray-500 text-[10px] sm:text-xs font-mono whitespace-nowrap">{time}</span>
        </div>

        {showExpandedMetadata ? (
          <div className="mt-3 pt-3 border-t border-gray-700/50">
            <pre className="text-xs text-gray-500 overflow-x-auto bg-gray-900/50 p-3 rounded-lg">
              {JSON.stringify(event.metadata || {}, null, 2)}
            </pre>
          </div>
        ) : null}

        {event.event_type === "code_diff" && event.metadata ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            className="mt-3 pt-3 border-t border-gray-700/50"
          >
            <div className="font-mono text-xs">
              <div className="text-gray-500 mb-2 flex items-center gap-2">
                <FileCode className="w-3 h-3" />
                {String(event.metadata.filepath || '')}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-red-500/10 p-2 rounded-lg overflow-x-auto border border-red-500/20">
                  <div className="text-red-400 text-xs mb-1 flex items-center gap-1">
                    <span>−</span> Before
                  </div>
                  <pre className="text-red-300/70">{String(event.metadata.before || '').substring(0, 200)}...</pre>
                </div>
                <div className="bg-green-500/10 p-2 rounded-lg overflow-x-auto border border-green-500/20">
                  <div className="text-green-400 text-xs mb-1 flex items-center gap-1">
                    <span>+</span> After
                  </div>
                  <pre className="text-green-300/70">{String(event.metadata.after || '').substring(0, 200)}...</pre>
                </div>
              </div>
            </div>
          </motion.div>
        ) : null}

        {event.event_type === "screenshot" && event.metadata?.screenshot_base64 ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            className="mt-3 pt-3 border-t border-gray-700/50"
          >
            <div className="relative rounded-lg overflow-hidden border border-indigo-500/30 bg-indigo-500/5">
              <div className="absolute top-2 left-2 bg-indigo-500/80 text-white text-xs px-2 py-1 rounded flex items-center gap-1 z-10">
                <Camera className="w-3 h-3" />
                Visual Capture
              </div>
              <img
                src={`data:image/png;base64,${event.metadata.screenshot_base64}`}
                alt="Screenshot"
                className="w-full h-auto rounded-lg"
              />
            </div>
          </motion.div>
        ) : null}

        {event.event_type === "visual_analysis" && event.metadata ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            className="mt-3 pt-3 border-t border-gray-700/50"
          >
            <div className="space-y-3">
              <div className="bg-violet-500/10 p-3 rounded-lg border border-violet-500/20">
                <div className="text-violet-400 text-xs font-semibold mb-1 flex items-center gap-1">
                  <Eye className="w-3 h-3" />
                  Gemini Vision Analysis
                </div>
                <p className="text-violet-300/80 text-sm">
                  {String(event.metadata.screenshot_description || 'No description available')}
                </p>
              </div>

             
              {Array.isArray(event.metadata.issues) && event.metadata.issues.length > 0 ? (
                <div className="space-y-2">
                  <div className="text-red-400 text-xs font-semibold flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Visual Issues Detected ({event.metadata.issues.length})
                  </div>
                  {(event.metadata.issues as Array<{type?: string; problem?: string; severity?: string; element?: string}>).map((issue, idx) => (
                    <div key={idx} className="bg-red-500/10 p-2 rounded-lg border border-red-500/20 text-xs">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                          issue.severity === 'high' ? 'bg-red-500 text-white' :
                          issue.severity === 'medium' ? 'bg-yellow-500 text-black' :
                          'bg-gray-500 text-white'
                        }`}>
                          {issue.severity || 'unknown'}
                        </span>
                        <span className="text-red-400 font-medium">{issue.type || 'unknown'}</span>
                      </div>
                      <p className="text-red-300/70">{issue.problem}</p>
                      {issue.element ? (
                        <p className="text-gray-500 mt-1">Element: {issue.element}</p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : event.metadata.has_issues === false ? (
                <div className="bg-green-500/10 p-2 rounded-lg border border-green-500/20 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  <span className="text-green-400">No visual issues detected!</span>
                </div>
              ) : null}

              
              {typeof event.metadata.confidence === 'number' ? (
                <div className="text-gray-500 text-xs">
                  Confidence: {Math.round(Number(event.metadata.confidence) * 100)}%
                </div>
              ) : null}
            </div>
          </motion.div>
        ) : null}

        {event.metadata?.pr_url ? (
          <motion.a
            href={String(event.metadata.pr_url)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 mt-3 px-4 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 transition-colors border border-cyan-500/30"
            onClick={(e) => e.stopPropagation()}
          >
            <LinkIcon className="w-4 h-4" />
            <span>View Pull Request</span>
          </motion.a>
        ) : null}
      </motion.div>
    </motion.div>
  );
}

function LoadingPulse() {
  return (
    <div className="relative pl-8">
      <motion.div
        className="absolute left-0 top-2 w-6 h-6 rounded-full bg-cyan-500 flex items-center justify-center"
        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        <Brain className="w-3 h-3 text-white" />
      </motion.div>
      <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
        <div className="flex items-center gap-3">
          <Loader2 className="w-4 h-4 text-cyan-500 animate-spin" />
          <span className="text-cyan-400 text-sm">TALOS is thinking...</span>
        </div>
      </div>
    </div>
  );
}

export default function Timeline({ runId, apiBaseUrl = "", onComplete }: TimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const eventSourceRef = useRef<EventSource | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    console.log(`[TALOS Timeline] Run ID changed to: ${runId}, resetting state...`);
    setEvents([]);
    setIsConnected(false);
    setIsComplete(false);
    setError(null);
    setIsLoadingHistory(true);

    if (eventSourceRef.current) {
      console.log(`[TALOS Timeline] Closing old SSE connection`);
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, [runId]);


  const currentRunIdRef = useRef<string>(runId);
  
  useEffect(() => {
    currentRunIdRef.current = runId;
  }, [runId]);

  useEffect(() => {
    if (containerRef.current && events.length > 0 && !isComplete) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events, isComplete]);

  useEffect(() => {
    if (!runId) return;

    const fetchHistory = async () => {
      setIsLoadingHistory(true);
      const fetchingRunId = runId; 
      console.log(`[TALOS Timeline] Fetching history for run: ${fetchingRunId}`);
      try {
        const res = await fetch(`${apiBaseUrl}/events/history/${fetchingRunId}`);
        
        if (currentRunIdRef.current !== fetchingRunId) {
          console.log(`[TALOS Timeline] Discarding stale history for ${fetchingRunId}, current is ${currentRunIdRef.current}`);
          return;
        }
        
        if (res.ok) {
          const data = await res.json();
          const historyEvents = (data.events || []).map((e: TimelineEvent & { run_id?: string }) => ({
            ...e,
            run_id: fetchingRunId,
          }));
          
          console.log(`[TALOS Timeline] Loaded ${historyEvents.length} events from history`);
          
          if (historyEvents.length > 0) {
            setEvents(historyEvents);
            
            const hasCompleted = historyEvents.some(
              (e: TimelineEvent) => e.event_type === "success" || e.event_type === "failure" || e.event_type === "mission_end"
            );
            if (hasCompleted) {
              console.log(`[TALOS Timeline] Run already complete`);
              setIsComplete(true);
              const status = historyEvents.some((e: TimelineEvent) => e.event_type === "success") ? "success" : "failure";
              onComplete?.(status);
            }
          }
        } else {
          console.error(`[TALOS Timeline] History fetch failed: ${res.status}`);
        }
      } catch (err) {
        console.error("[TALOS Timeline] Failed to fetch history:", err);
      } finally {
      
        if (currentRunIdRef.current === fetchingRunId) {
          setIsLoadingHistory(false);
        }
      }
    };

    fetchHistory();
  }, [runId, apiBaseUrl, onComplete]);

  useEffect(() => {
    if (!runId || isComplete || isLoadingHistory) return;

    const url = `${apiBaseUrl}/events/stream/${runId}`;
    console.log(`[TALOS Timeline] Connecting to SSE: ${url}`);
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log(`[TALOS Timeline] SSE connection opened`);
      setIsConnected(true);
      setError(null);
    };

    eventSource.onerror = (e) => {
      console.error(`[TALOS Timeline] SSE error:`, e);
      setError("Connection lost. Retrying...");
      setIsConnected(false);
    };
    const seenTimestamps = new Set<string>();

    const eventTypes = Object.keys(EVENT_CONFIG);
    eventTypes.forEach((eventType) => {
      eventSource.addEventListener(eventType, (e) => {
        try {
          const data = JSON.parse(e.data) as TimelineEvent;
          
          if (seenTimestamps.has(data.timestamp)) return;
          seenTimestamps.add(data.timestamp);
          
          setEvents((prev) => {
            if (prev.some(p => p.timestamp === data.timestamp)) return prev;
            console.log(`[TALOS Timeline] New event: ${eventType} - ${data.title}`);
            return [...prev, data];
          });

          if (eventType === "mission_end" || eventType === "success" || eventType === "failure") {
            setIsComplete(true);
            onComplete?.(eventType === "success" ? "success" : "failure");
            eventSource.close();
          }
        } catch (err) {
          console.error("Failed to parse event:", err);
        }
      });
    });

    eventSource.addEventListener("connected", () => {
      setIsConnected(true);
    });

    eventSource.addEventListener("complete", () => {
      setIsComplete(true);
      eventSource.close();
    });

    return () => {
      eventSource.close();
    };
  }, [runId, apiBaseUrl, isComplete, isLoadingHistory]);

  const eventsLengthRef = useRef(0);
  useEffect(() => {
    eventsLengthRef.current = events.length;
  }, [events.length]);

  useEffect(() => {
    if (isConnected || isComplete || isLoadingHistory || !runId) return;

    const pollingRunId = runId; 
    
    const pollDelay = setTimeout(() => {
      const pollInterval = setInterval(async () => {
    
        if (currentRunIdRef.current !== pollingRunId) {
          console.log(`[TALOS Timeline] Stopping stale polling for ${pollingRunId}`);
          clearInterval(pollInterval);
          return;
        }
        
        try {
          const res = await fetch(`${apiBaseUrl}/events/history/${pollingRunId}`);
          
        
          if (currentRunIdRef.current !== pollingRunId) {
            clearInterval(pollInterval);
            return;
          }
          
          if (res.ok) {
            const data = await res.json();
            const historyEvents = (data.events || []).map((e: TimelineEvent & { run_id?: string }) => ({
              ...e,
              run_id: pollingRunId,
            }));
            
           
            if (historyEvents.length > eventsLengthRef.current) {
              setEvents(historyEvents);
              
              const hasCompleted = historyEvents.some(
                (e: TimelineEvent) => e.event_type === "success" || e.event_type === "failure" || e.event_type === "mission_end"
              );
              if (hasCompleted) {
                setIsComplete(true);
                const status = historyEvents.some((e: TimelineEvent) => e.event_type === "success") ? "success" : "failure";
                onComplete?.(status);
                clearInterval(pollInterval);
              }
            }
          }
        } catch (err) {
          console.error("Polling failed:", err);
        }
      }, 3000);

      return () => clearInterval(pollInterval);
    }, 5000); 

    return () => clearTimeout(pollDelay);
  }, [runId, apiBaseUrl, isConnected, isComplete, isLoadingHistory, onComplete]);

  if (!runId) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>No active healing run. Waiting for webhook trigger...</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-6 px-4">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${isConnected ? "bg-emerald-500" : "bg-amber-500"} animate-pulse`} />
          <span className="text-sm text-gray-400">
            {isConnected ? "Connected to Neural Stream" : "Connecting..."}
          </span>
        </div>
        <div className="font-mono text-xs text-gray-500 flex items-center gap-2">
          <Dna className="w-3 h-3" />
          Run: {runId.slice(0, 12)}...
        </div>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mb-4 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm flex items-center gap-2"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto px-4 pb-4 scroll-smooth"
        style={{ maxHeight: "calc(100vh - 200px)" }}
      >
        <AnimatePresence mode="popLayout">
          {events.map((event, index) => (
            <TimelineEventCard
              key={`${event.timestamp}-${index}`}
              event={event}
              isLatest={index === events.length - 1 && !isComplete}
            />
          ))}
        </AnimatePresence>

        {isConnected && !isComplete && events.length > 0 && <LoadingPulse />}

        {isLoadingHistory && events.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-48 text-gray-500"
          >
            <div className="w-16 h-16 mb-4 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
            </div>
            <p className="text-gray-400">Loading run history...</p>
          </motion.div>
        )}

        {events.length === 0 && !isLoadingHistory && isConnected && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-48 text-gray-500"
          >
            <div className="w-16 h-16 mb-4 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              >
                <Dna className="w-8 h-8 text-cyan-400" />
              </motion.div>
            </div>
            <p className="text-gray-400">TALOS is awakening...</p>
          </motion.div>
        )}

        {events.length === 0 && !isLoadingHistory && !isConnected && !isComplete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-48 text-gray-500"
          >
            <div className="w-16 h-16 mb-4 rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/30 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-amber-400" />
            </div>
            <p className="text-gray-400">Run details not available</p>
            <p className="text-gray-500 text-sm mt-1">Event history may have expired</p>
          </motion.div>
        )}

        {isComplete && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-8 text-center"
          >
            <div className={`inline-flex items-center gap-3 px-6 py-3 rounded-xl border ${
              events.some(e => e.event_type === "success") 
                ? "bg-emerald-500/10 border-emerald-500/30" 
                : "bg-red-500/10 border-red-500/30"
            }`}>
              {events.some(e => e.event_type === "success") 
                ? <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                : <XCircle className="w-5 h-5 text-red-400" />
              }
              <span className={events.some(e => e.event_type === "success") ? "text-emerald-400" : "text-red-400"}>
                Healing {events.some(e => e.event_type === "success") ? "Complete" : "Failed"}
              </span>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
