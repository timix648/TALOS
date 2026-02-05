"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import Link from "next/link";

interface Repository {
  full_name: string;
  name: string;
  private: boolean;
  default_branch: string;
  description: string | null;
  watched: boolean;
  auto_heal_enabled: boolean;
  safe_mode: boolean;
}

interface UserSession {
  logged_in: boolean;
  user?: {
    login: string;
    avatar_url: string;
    name: string;
  };
  installation_id?: number;
  has_installation?: boolean;
}

export default function RepositoriesPage() {
  const [session, setSession] = useState<UserSession | null>(null);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "watched" | "unwatched">("all");
  const [search, setSearch] = useState("");

  const GITHUB_APP_URL = process.env.NEXT_PUBLIC_GITHUB_APP_URL || "https://github.com/apps/talos-healer/installations/new";

  // Fetch session
  useEffect(() => {
    const fetchSession = async () => {
      try {
        const res = await fetch("/api/auth/session");
        const data = await res.json();
        setSession(data);
        if (!data.logged_in) {
          setLoading(false);
        }
      } catch (error) {
        console.error("Session fetch error:", error);
        setLoading(false);
      }
    };
    fetchSession();
  }, []);

  // Fetch repos when we have installation_id
  useEffect(() => {
    const fetchRepos = async () => {
      if (!session?.installation_id) {
        setLoading(false);
        return;
      }

      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${API_URL}/installations/${session.installation_id}/repos`);
        if (res.ok) {
          const data = await res.json();
          setRepos(data.repositories || []);
        }
      } catch (error) {
        console.error("Repos fetch error:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchRepos();
  }, [session]);

  // Toggle watch status
  const toggleWatch = async (repo: Repository) => {
    if (!session?.installation_id) return;
    setUpdating(repo.full_name);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      if (repo.watched) {
        // Unwatch
        const [owner, name] = repo.full_name.split("/");
        await fetch(`${API_URL}/installations/${session.installation_id}/watch/${owner}/${name}`, {
          method: "DELETE",
        });
      } else {
        // Watch
        await fetch(`${API_URL}/installations/${session.installation_id}/watch`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            repo_full_name: repo.full_name,
            auto_heal_enabled: true,
            safe_mode: true,
          }),
        });
      }

      // Update local state
      setRepos(repos.map(r => 
        r.full_name === repo.full_name 
          ? { ...r, watched: !r.watched, auto_heal_enabled: !r.watched }
          : r
      ));
    } catch (error) {
      console.error("Toggle watch error:", error);
    } finally {
      setUpdating(null);
    }
  };

  // Filter repos
  const filteredRepos = repos.filter(repo => {
    const matchesFilter = 
      filter === "all" ? true :
      filter === "watched" ? repo.watched :
      !repo.watched;
    
    const matchesSearch = 
      search === "" || 
      repo.full_name.toLowerCase().includes(search.toLowerCase()) ||
      repo.description?.toLowerCase().includes(search.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const watchedCount = repos.filter(r => r.watched).length;

  // Not logged in state
  if (!loading && !session?.logged_in) {
    return (
      <main className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <div className="text-6xl mb-6">🔐</div>
          <h1 className="text-2xl font-bold mb-4">Sign In Required</h1>
          <p className="text-gray-400 mb-8">
            Sign in with GitHub to view and manage your repositories.
          </p>
          <a
            href="/api/auth/login"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-xl font-bold hover:opacity-90 transition-all"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            Sign in with GitHub
          </a>
        </motion.div>
      </main>
    );
  }

  // Logged in but no installation
  if (!loading && session?.logged_in && !session.has_installation) {
    return (
      <main className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <div className="text-6xl mb-6">🔗</div>
          <h1 className="text-2xl font-bold mb-4">Install TALOS App</h1>
          <p className="text-gray-400 mb-8">
            You're signed in as <strong>@{session.user?.login}</strong>. Now install the TALOS GitHub App to give it access to your repositories.
          </p>
          <a
            href={GITHUB_APP_URL}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-xl font-bold hover:opacity-90 transition-all"
          >
            🔗 Install TALOS App
          </a>
          <p className="text-gray-500 text-sm mt-4">
            After installing, refresh this page.
          </p>
        </motion.div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <nav className="sticky top-0 z-50 backdrop-blur-md bg-gray-950/80 border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center">
                <span className="text-sm">🧬</span>
              </div>
              <span className="font-bold">TALOS</span>
            </Link>
            <span className="text-gray-600">/</span>
            <span className="text-gray-400">Repositories</span>
          </div>
          
          {session?.user && (
            <div className="flex items-center gap-3">
              <img 
                src={session.user.avatar_url} 
                alt={session.user.login}
                className="w-8 h-8 rounded-full"
              />
              <span className="text-sm text-gray-400">{session.user.login}</span>
            </div>
          )}
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Title & Stats */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold">Your Repositories</h1>
            <p className="text-gray-400 mt-1">
              {watchedCount} of {repos.length} repos protected by TALOS
            </p>
          </div>
          
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-700 rounded-lg hover:bg-gray-800 transition-all"
          >
            📊 Dashboard
          </Link>
        </div>

        {/* Search & Filter */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
            <input
              type="text"
              placeholder="Search repositories..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
          
          <div className="flex gap-2">
            {(["all", "watched", "unwatched"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  filter === f
                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/50"
                    : "bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600"
                }`}
              >
                {f === "all" ? "All" : f === "watched" ? "🛡️ Watching" : "⏸️ Not Watching"}
              </button>
            ))}
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <motion.div
              className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            />
          </div>
        )}

        {/* Repo List */}
        {!loading && (
          <div className="space-y-3">
            <AnimatePresence mode="popLayout">
              {filteredRepos.map((repo, i) => (
                <motion.div
                  key={repo.full_name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: i * 0.03 }}
                  className={`p-4 rounded-xl border transition-all ${
                    repo.watched
                      ? "bg-cyan-500/5 border-cyan-500/30"
                      : "bg-gray-800/50 border-gray-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{repo.private ? "🔒" : "📂"}</span>
                        <a 
                          href={`https://github.com/${repo.full_name}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-white hover:text-cyan-400 truncate"
                        >
                          {repo.full_name}
                        </a>
                        {repo.watched && (
                          <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs rounded-full border border-cyan-500/30">
                            🛡️ Protected
                          </span>
                        )}
                      </div>
                      {repo.description && (
                        <p className="text-sm text-gray-500 mt-1 truncate">{repo.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>📌 {repo.default_branch}</span>
                        {repo.watched && repo.safe_mode && (
                          <span className="text-green-400">✅ Safe Mode (PR only)</span>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => toggleWatch(repo)}
                      disabled={updating === repo.full_name}
                      className={`flex-shrink-0 px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                        repo.watched
                          ? "bg-gray-700 text-gray-300 hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/50"
                          : "bg-gradient-to-r from-cyan-500 to-purple-600 text-white hover:opacity-90"
                      } ${updating === repo.full_name ? "opacity-50 cursor-wait" : ""}`}
                    >
                      {updating === repo.full_name ? (
                        <motion.span
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          className="inline-block"
                        >
                          ⏳
                        </motion.span>
                      ) : repo.watched ? (
                        "Stop Watching"
                      ) : (
                        "🛡️ Enable TALOS"
                      )}
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {filteredRepos.length === 0 && !loading && (
              <div className="text-center py-20 text-gray-500">
                <div className="text-4xl mb-4">📭</div>
                <p>No repositories match your filter</p>
              </div>
            )}
          </div>
        )}

        {/* Info Footer */}
        <div className="mt-12 p-4 bg-gray-800/50 border border-gray-700 rounded-xl">
          <h3 className="font-medium mb-2">💡 How it works</h3>
          <ul className="text-sm text-gray-400 space-y-1">
            <li>• <strong>Protected repos</strong> are monitored for CI/CD failures</li>
            <li>• When a build fails, TALOS analyzes the error and opens a fix PR</li>
            <li>• <strong>Safe Mode</strong> means TALOS only creates PRs, never pushes directly</li>
            <li>• You can change access permissions in <a href="https://github.com/settings/installations" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">GitHub Settings</a></li>
          </ul>
        </div>
      </div>
    </main>
  );
}
