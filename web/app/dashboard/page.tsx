"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Shield,
  Activity,
  GitBranch,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Zap,
  Eye,
  GitPullRequest,
  Settings,
  ChevronRight,
  Radio,
  Search,
  AlertTriangle,
  Wrench,
  TestTube,
  Send,
  Home,
  ExternalLink,
  RotateCcw,
} from "lucide-react";
import Timeline from "@/components/timeline";

interface HealingRun {
  id: string;
  repo: string;
  status: "running" | "success" | "failure";
  timestamp: string;
  pr_url?: string;
}

interface WatchedRepo {
  full_name: string;
  status: "healthy" | "healing" | "error";
  last_checked?: string;
  total_heals?: number;
}

// Status badge with icons instead of emojis
function StatusBadge({ status }: { status: HealingRun["status"] }) {
  const config = {
    running: {
      bg: "bg-cyan-500/10",
      border: "border-cyan-500/30",
      text: "text-cyan-400",
      icon: Loader2,
      iconClass: "animate-spin",
    },
    success: {
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/30",
      text: "text-emerald-400",
      icon: CheckCircle2,
      iconClass: "",
    },
    failure: {
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      text: "text-red-400",
      icon: XCircle,
      iconClass: "",
    },
  };

  const { bg, border, text, icon: Icon, iconClass } = config[status];

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${bg} ${border} ${text}`}>
      <Icon className={`w-3 h-3 ${iconClass}`} />
      <span className="capitalize">{status}</span>
    </span>
  );
}

// Run card component
function RunCard({ run, isActive, onClick }: { 
  run: HealingRun; 
  isActive: boolean;
  onClick: () => void;
}) {
  const time = new Date(run.timestamp).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <motion.button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-xl border transition-all ${
        isActive 
          ? "bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border-cyan-500/50 shadow-lg shadow-cyan-500/5" 
          : "bg-gray-800/30 border-gray-700/50 hover:border-gray-600 hover:bg-gray-800/50"
      }`}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      layout
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="font-medium text-white truncate flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-gray-400 flex-shrink-0" />
            {run.repo}
          </div>
          <div className="text-sm text-gray-500 font-mono mt-1">#{run.id.slice(0, 8)}</div>
        </div>
        <StatusBadge status={run.status} />
      </div>
      <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {time}
        </span>
        {run.pr_url && (
          <a 
            href={run.pr_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            onClick={(e) => e.stopPropagation()}
          >
            <GitPullRequest className="w-3 h-3" />
            View PR
          </a>
        )}
      </div>
    </motion.button>
  );
}

// Protected repo card
function ProtectedRepoCard({ repo }: { repo: WatchedRepo }) {
  const statusConfig = {
    healthy: { icon: Shield, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    healing: { icon: Loader2, color: "text-cyan-400", bg: "bg-cyan-500/10", spin: true },
    error: { icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-500/10" },
  };

  const config = statusConfig[repo.status];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3 p-3 rounded-lg bg-gray-800/30 border border-gray-700/50 hover:border-gray-600 transition-colors"
    >
      <div className={`p-2 rounded-lg ${config.bg}`}>
        <Icon className={`w-4 h-4 ${config.color} ${'spin' in config && config.spin ? 'animate-spin' : ''}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white truncate">{repo.full_name}</div>
        <div className="text-xs text-gray-500">
          {repo.total_heals || 0} heals performed
        </div>
      </div>
      <ChevronRight className="w-4 h-4 text-gray-500" />
    </motion.div>
  );
}

// Healing pipeline visualization
function HealingPipelineVisualization() {
  const stages = [
    { id: 1, name: "Detect", icon: AlertTriangle, description: "CI/CD failure detected via webhook" },
    { id: 2, name: "Analyze", icon: Search, description: "Parse logs & identify root cause" },
    { id: 3, name: "Diagnose", icon: Zap, description: "AI reasoning with Gemini" },
    { id: 4, name: "Fix", icon: Wrench, description: "Generate & apply code patch" },
    { id: 5, name: "Verify", icon: TestTube, description: "Run tests in sandbox" },
    { id: 6, name: "Deploy", icon: Send, description: "Create PR with fix" },
  ];

  return (
    <div className="relative">
      <div className="flex items-center justify-between">
        {stages.map((stage, index) => (
          <div key={stage.id} className="flex items-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="flex flex-col items-center group"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 flex items-center justify-center group-hover:border-cyan-500/50 transition-colors cursor-pointer relative">
                <stage.icon className="w-5 h-5 text-gray-400 group-hover:text-cyan-400 transition-colors" />
                <div className="absolute -bottom-16 left-1/2 -translate-x-1/2 w-32 p-2 bg-gray-900 border border-gray-700 rounded-lg text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                  {stage.description}
                </div>
              </div>
              <span className="text-xs text-gray-400 mt-2 font-medium">{stage.name}</span>
            </motion.div>
            {index < stages.length - 1 && (
              <motion.div
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: index * 0.1 + 0.05 }}
                className="w-6 lg:w-10 h-0.5 bg-gradient-to-r from-gray-700 to-gray-600 mx-1"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// Empty state with better design
function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center h-full text-center p-8"
    >
      <motion.div
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200 }}
        className="w-20 h-20 mb-6 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center"
      >
        <Activity className="w-10 h-10 text-cyan-400" />
      </motion.div>
      
      <h3 className="text-xl font-bold text-white mb-2">Ready & Watching</h3>
      <p className="text-gray-400 max-w-md mb-8">
        TALOS is actively monitoring your repositories. When a CI/CD pipeline fails, 
        the autonomous healing process will begin automatically.
      </p>
      
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 max-w-2xl w-full">
        <h4 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          How TALOS Works
        </h4>
        <HealingPipelineVisualization />
      </div>
      
      <Link
        href="/repositories"
        className="mt-8 px-6 py-3 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-xl font-medium hover:opacity-90 transition-all flex items-center gap-2 shadow-lg shadow-cyan-500/20"
      >
        <Settings className="w-4 h-4" />
        Manage Repositories
      </Link>
    </motion.div>
  );
}

// Live indicator
function LiveIndicator() {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-full">
      <motion.div
        className="w-2 h-2 bg-emerald-500 rounded-full"
        animate={{ scale: [1, 1.2, 1], opacity: [0.7, 1, 0.7] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      />
      <span className="text-xs text-emerald-400 font-medium">Live</span>
    </div>
  );
}

// Stats card
function StatCard({ label, value, icon: Icon, color }: { 
  label: string; 
  value: string | number; 
  icon: React.ElementType;
  color: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-4"
    >
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="text-2xl font-bold text-white">{value}</div>
          <div className="text-sm text-gray-400">{label}</div>
        </div>
      </div>
    </motion.div>
  );
}

export default function Dashboard() {
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runs, setRuns] = useState<HealingRun[]>([]);
  const [watchedRepos, setWatchedRepos] = useState<WatchedRepo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [retryAllowed, setRetryAllowed] = useState<string | null>(null); // repo that can retry
  const [stats, setStats] = useState({
    total_heals: 0,
    successful_heals: 0,
    fix_rate_percent: 0,
    avg_boot_time_ms: 0,
  });
  
  // Use refs to avoid stale closures in polling
  const lastKnownRunIdRef = useRef<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Fetch stats from backend
  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_URL}/stats/`);
      if (res.ok) {
        const data = await res.json();
        setStats({
          total_heals: data.total_heals || 0,
          successful_heals: data.successful_heals || 0,
          fix_rate_percent: data.fix_rate_percent || 0,
          avg_boot_time_ms: data.avg_boot_time_ms || 0,
        });
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  // Allow TALOS to push another fix
  const handleAllowRetry = async () => {
    if (!activeRunId) return;
    
    try {
      const response = await fetch(`${API_URL}/runs/${activeRunId}/allow-retry`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setRetryAllowed(data.repo);
        // Clear after 30 seconds
        setTimeout(() => setRetryAllowed(null), 30000);
      }
    } catch (error) {
      console.error("Failed to allow retry:", error);
    }
  };

  // Fetch runs (separated for polling)
  const fetchRuns = async (isInitial = false) => {
    try {
      const runsRes = await fetch(`${API_URL}/runs/`);
      if (runsRes.ok) {
        const runsData = await runsRes.json();
        // Map API response to frontend interface
        const newRuns: HealingRun[] = (runsData.runs || []).map((r: { 
          run_id: string; 
          repo_full_name: string; 
          status: string; 
          started_at: string;
          pr_url?: string;
        }) => ({
          id: r.run_id,
          repo: r.repo_full_name,
          status: r.status as "running" | "success" | "failure",
          timestamp: r.started_at,
          pr_url: r.pr_url,
        }));
        setRuns(newRuns);
        
        // Auto-select only for NEW running runs (live healing in progress)
        const runningRun = newRuns.find((r: HealingRun) => r.status === "running");
        
        if (runningRun && runningRun.id !== lastKnownRunIdRef.current) {
          // New running run detected - auto-show it (live event)
          console.log("🚨 New healing run detected:", runningRun.id);
          setActiveRunId(runningRun.id);
          lastKnownRunIdRef.current = runningRun.id;
        } else if (isInitial && newRuns[0]) {
          // Initial load only - select latest run
          setActiveRunId(newRuns[0].id);
          lastKnownRunIdRef.current = newRuns[0].id;
        }
        // NOTE: Don't auto-switch for completed runs during polling
        // User's manual selection should be preserved
      }
    } catch (error) {
      console.error("Failed to fetch runs:", error);
    }
  };

  // Fetch watched repos
  const fetchWatchedRepos = async () => {
    try {
      const sessionRes = await fetch('/api/auth/session');
      if (sessionRes.ok) {
        const sessionData = await sessionRes.json();
        if (sessionData.installation_id) {
          const reposRes = await fetch(`${API_URL}/installations/${sessionData.installation_id}/repos`);
          if (reposRes.ok) {
            const reposData = await reposRes.json();
            const watched = (reposData.repositories || [])
              .filter((r: { watched: boolean }) => r.watched)
              .map((r: { full_name: string }) => ({
                full_name: r.full_name,
                status: "healthy" as const,
                total_heals: 0,
              }));
            setWatchedRepos(watched);
          }
        }
      }
    } catch (error) {
      console.error("Failed to fetch repos:", error);
    }
  };

  // Initial data fetch
  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true);
      await Promise.all([fetchRuns(true), fetchWatchedRepos(), fetchStats()]);
      setIsLoading(false);
    };
    loadInitialData();

    // Check URL for run_id parameter
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const urlRunId = params.get('run_id');
      if (urlRunId) setActiveRunId(urlRunId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Poll for new runs every 5 seconds (real-time updates)
  useEffect(() => {
    const pollInterval = setInterval(() => {
      fetchRuns(false);
      fetchStats();  // Also refresh stats
    }, 5000);

    return () => clearInterval(pollInterval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // No dependencies - runs once on mount, uses refs for current values

  // Handle completion
  const handleComplete = (status: "success" | "failure") => {
    if (activeRunId) {
      setRuns(prev => prev.map(r => 
        r.id === activeRunId ? { ...r, status } : r
      ));
      // Refresh stats when a run completes
      fetchStats();
    }
  };

  const runningCount = runs.filter(r => r.status === "running").length;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-gray-950/80 border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/" className="flex items-center gap-3 group">
                <motion.div 
                  className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/20"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Shield className="w-5 h-5 text-white" />
                </motion.div>
                <div>
                  <span className="text-xl font-bold">TALOS</span>
                  <span className="hidden sm:block text-xs text-gray-500">Neural Dashboard</span>
                </div>
              </Link>
            </div>
            
            <div className="flex items-center gap-3">
              <LiveIndicator />
              <Link
                href="/"
                className="hidden sm:flex items-center gap-2 text-gray-400 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-gray-800/50"
              >
                <Home className="w-4 h-4" />
                Home
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Stats Row */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        >
          <StatCard 
            label="Protected Repos" 
            value={watchedRepos.length} 
            icon={Shield} 
            color="bg-cyan-500/10 text-cyan-400" 
          />
          <StatCard 
            label="Successful Heals" 
            value={stats.successful_heals} 
            icon={CheckCircle2} 
            color="bg-emerald-500/10 text-emerald-400" 
          />
          <StatCard 
            label="Total Heals" 
            value={stats.total_heals} 
            icon={Activity} 
            color="bg-purple-500/10 text-purple-400" 
          />
          <StatCard 
            label="Success Rate" 
            value={`${stats.fix_rate_percent}%`} 
            icon={Zap} 
            color="bg-amber-500/10 text-amber-400" 
          />
        </motion.div>

        <div className="grid lg:grid-cols-12 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-3 space-y-6">
            {/* Protected Repos */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-gray-900/50 border border-gray-800 rounded-2xl p-4"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-200 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-cyan-400" />
                  Protected Repos
                </h2>
                <Link href="/repositories" className="text-xs text-cyan-400 hover:text-cyan-300">
                  Manage
                </Link>
              </div>
              
              {isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-16 bg-gray-800/50 rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : watchedRepos.length > 0 ? (
                <div className="space-y-2">
                  {watchedRepos.map((repo) => (
                    <ProtectedRepoCard key={repo.full_name} repo={repo} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500 text-sm">
                  <Eye className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No repos being watched</p>
                  <Link href="/repositories" className="text-cyan-400 hover:underline text-xs mt-1 block">
                    Add repositories
                  </Link>
                </div>
              )}
            </motion.div>

            {/* Healing Runs */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gray-900/50 border border-gray-800 rounded-2xl p-4"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-200 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-purple-400" />
                  Healing Runs
                </h2>
                <span className="text-xs text-gray-500">{runs.length} total</span>
              </div>

              {isLoading ? (
                <div className="space-y-2">
                  {[1, 2].map(i => (
                    <div key={i} className="h-24 bg-gray-800/50 rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : runs.length > 0 ? (
                <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                  <AnimatePresence>
                    {runs.map((run) => (
                      <RunCard
                        key={run.id}
                        run={run}
                        isActive={run.id === activeRunId}
                        onClick={() => setActiveRunId(run.id)}
                      />
                    ))}
                  </AnimatePresence>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500 text-sm">
                  <Radio className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Waiting for events...</p>
                  <p className="text-xs mt-1">Push code or trigger a build failure</p>
                </div>
              )}
            </motion.div>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gray-900/50 border border-gray-800 rounded-2xl p-4"
            >
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Quick Actions
              </h3>
              <div className="space-y-2">
                <Link
                  href="/repositories"
                  className="w-full px-4 py-3 text-left text-sm bg-gray-800/50 hover:bg-gray-800 rounded-xl transition-colors flex items-center gap-3 group"
                >
                  <div className="p-2 rounded-lg bg-purple-500/10 group-hover:bg-purple-500/20 transition-colors">
                    <Settings className="w-4 h-4 text-purple-400" />
                  </div>
                  <div>
                    <div className="font-medium text-white">Manage Repositories</div>
                    <div className="text-xs text-gray-500">Add or remove watched repos</div>
                  </div>
                </Link>
                <a
                  href="https://github.com/apps/talos-healer/installations/new"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full px-4 py-3 text-left text-sm bg-gray-800/50 hover:bg-gray-800 rounded-xl transition-colors flex items-center gap-3 group"
                >
                  <div className="p-2 rounded-lg bg-cyan-500/10 group-hover:bg-cyan-500/20 transition-colors">
                    <ExternalLink className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div>
                    <div className="font-medium text-white">Manage Installations</div>
                    <div className="text-xs text-gray-500">GitHub App settings</div>
                  </div>
                </a>
              </div>
            </motion.div>
          </aside>

          {/* Main Content */}
          <main className="lg:col-span-9">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-900/50 border border-gray-800 rounded-2xl overflow-hidden min-h-[600px]"
            >
              {/* Terminal header */}
              <div className="flex items-center justify-between px-4 py-3 bg-gray-900/80 border-b border-gray-800">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                </div>
                <span className="text-sm text-gray-400 font-mono">
                  {activeRunId ? `talos://run/${activeRunId.slice(0, 12)}` : "talos://neural-stream"}
                </span>
                {/* Allow Retry Button - shows when active run completed with success */}
                {activeRunId && runs.find(r => r.id === activeRunId)?.status === "success" ? (
                  retryAllowed ? (
                    <span className="text-xs text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Retry allowed
                    </span>
                  ) : (
                    <button
                      onClick={handleAllowRetry}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-orange-500/10 border border-orange-500/30 text-orange-400 rounded-lg hover:bg-orange-500/20 transition-colors"
                    >
                      <RotateCcw className="w-3 h-3" />
                      Allow New Fix
                    </button>
                  )
                ) : (
                  <div className="w-24" />
                )}
              </div>

              {/* Timeline */}
              <div className="p-6">
                {activeRunId ? (
                  <Timeline
                    runId={activeRunId}
                    apiBaseUrl={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                    onComplete={handleComplete}
                  />
                ) : (
                  <EmptyState />
                )}
              </div>
            </motion.div>
          </main>
        </div>
      </div>
    </div>
  );
}
