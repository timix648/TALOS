"use client";

import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { useState, useEffect, useMemo } from "react";

interface UserSession {
  logged_in: boolean;
  user?: {
    id: number;
    login: string;
    avatar_url: string;
    name: string;
  };
  installation_id?: number;
  has_installation?: boolean;
}

function ParticleField() {
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);

  const particles = useMemo(() => {
    if (!mounted) return [];
    const width = window.innerWidth;
    const height = window.innerHeight;
    return [...Array(30)].map(() => ({
      initialX: Math.random() * width,
      initialY: Math.random() * height,
      targetX: Math.random() * width,
      targetY: Math.random() * height,
      duration: Math.random() * 10 + 10,
    }));
  }, [mounted]);

  if (!mounted) return null;

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((particle, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-cyan-500/30 rounded-full"
          initial={{ x: particle.initialX, y: particle.initialY }}
          animate={{ x: particle.targetX, y: particle.targetY, opacity: [0.2, 0.8, 0.2] }}
          transition={{ duration: particle.duration, repeat: Infinity, ease: "linear" }}
        />
      ))}
    </div>
  );
}

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [session, setSession] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const GITHUB_APP_URL = process.env.NEXT_PUBLIC_GITHUB_APP_URL || "https://github.com/apps/talos-healer/installations/new";

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const res = await fetch('/api/auth/session');
        const data = await res.json();
        setSession(data);
      } catch {
        setSession({ logged_in: false });
      } finally {
        setIsLoading(false);
      }
    };
    fetchSession();
  }, []);

  // Handle logout
  const handleLogout = async () => {
    await fetch('/api/auth/session', { method: 'DELETE' });
    setSession({ logged_in: false });
    window.location.href = '/';
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col">
      <ParticleField />
      
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-gray-950/80 border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <motion.div 
            className="flex items-center gap-3"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center">
              <span className="text-xl">🧬</span>
            </div>
            <span className="text-xl font-bold">TALOS</span>
          </motion.div>
          
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
          
          <motion.div 
            className="hidden md:flex items-center gap-6"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            {session?.has_installation && (
              <>
                <Link href="/dashboard" className="text-gray-400 hover:text-white transition-colors">
                  Dashboard
                </Link>
                <Link href="/repositories" className="text-gray-400 hover:text-white transition-colors">
                  Repositories
                </Link>
              </>
            )}
            
            {isLoading ? (
              <div className="w-24 h-9 bg-gray-800 rounded-lg animate-pulse" />
            ) : session?.logged_in ? (
              <div className="flex items-center gap-3">
                {!session.has_installation && (
                  <a 
                    href={GITHUB_APP_URL}
                    className="px-3 py-1.5 text-sm bg-yellow-500/20 text-yellow-400 border border-yellow-500/50 rounded-lg hover:bg-yellow-500/30 transition-colors"
                  >
                    Install App
                  </a>
                )}
                <div className="flex items-center gap-2">
                  <img 
                    src={session.user?.avatar_url} 
                    alt={session.user?.login}
                    className="w-8 h-8 rounded-full border-2 border-gray-700"
                  />
                  <span className="text-sm text-gray-300">{session.user?.login}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-gray-500 hover:text-red-400 text-sm transition-colors"
                >
                  Logout
                </button>
              </div>
            ) : (
              <a 
                href="/api/auth/login"
                className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                Sign in with GitHub
              </a>
            )}
          </motion.div>
        </div>
        
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t border-gray-800 px-4 py-4 space-y-3"
            >
              {session?.has_installation && (
                <>
                  <Link href="/dashboard" className="block text-gray-400 hover:text-white" onClick={() => setMobileMenuOpen(false)}>
                    Dashboard
                  </Link>
                  <Link href="/repositories" className="block text-gray-400 hover:text-white" onClick={() => setMobileMenuOpen(false)}>
                    Repositories
                  </Link>
                </>
              )}
              {session?.logged_in ? (
                <>
                  <div className="flex items-center gap-2 py-2 border-t border-gray-800">
                    <img src={session.user?.avatar_url} alt="" className="w-8 h-8 rounded-full" />
                    <span className="text-sm">{session.user?.login}</span>
                  </div>
                  {!session.has_installation && (
                    <a href={GITHUB_APP_URL} className="block px-4 py-2 bg-yellow-500/20 text-yellow-400 rounded-lg text-center">
                      Install TALOS App
                    </a>
                  )}
                  <button onClick={handleLogout} className="block w-full text-left text-red-400 hover:text-red-300">
                    Logout
                  </button>
                </>
              ) : (
                <a href="/api/auth/login" className="block px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg text-center font-medium">
                  Sign in with GitHub
                </a>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      <section className="flex-1 flex items-center justify-center px-4 sm:px-6 pt-20 pb-24">
        <div className="max-w-4xl mx-auto text-center z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-full mb-8"
          >
            <span className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
            <span className="text-cyan-400 text-sm font-medium">Vetrox Agentic 3.0 Hackathon</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl sm:text-7xl md:text-8xl font-bold mb-6"
          >
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400">
              TALOS
            </span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-xl sm:text-2xl md:text-3xl text-gray-300 mb-4"
          >
            The Self-Healing DevOps Species
          </motion.p>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-gray-500 mb-10"
          >
            Autonomous CI/CD repair powered by Gemini 3
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            {isLoading ? (
              <div className="px-8 py-4 bg-gray-800 rounded-xl animate-pulse w-48 h-14" />
            ) : session?.logged_in ? (
              session.has_installation ? (
                <Link
                  href="/dashboard"
                  className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-xl font-bold text-lg hover:opacity-90 transition-opacity"
                >
                  Dashboard
                </Link>
              ) : (
                <a
                  href={GITHUB_APP_URL}
                  className="px-8 py-4 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-xl font-bold text-lg hover:opacity-90 transition-opacity"
                >
                  Install TALOS on Your Repos
                </a>
              )
            ) : (
              <a
                href="/api/auth/login"
                className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-xl font-bold text-lg hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                Sign in with GitHub
              </a>
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="mt-16 grid grid-cols-3 gap-4 max-w-2xl mx-auto"
          >
            {[
              { icon: "👁️", label: "Observe" },
              { icon: "🧠", label: "Reason" },
              { icon: "🔧", label: "Heal" },
            ].map((step) => (
              <div key={step.label} className="text-center">
                <div className="text-3xl mb-2">{step.icon}</div>
                <div className="text-sm text-gray-400">{step.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      <footer className="border-t border-gray-800 py-6 px-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <span>🧬</span>
            <span>TALOS</span>
            <span className="text-gray-700">|</span>
            <span>Vetrox Agentic 3.0</span>
          </div>
          
          <div className="flex items-center gap-4">
            <a href="https://github.com/talos-agent/talos" target="_blank" className="text-gray-500 hover:text-white transition-colors" title="GitHub">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            </a>
            <a href="https://x.com/talos_agent" target="_blank" className="text-gray-500 hover:text-white transition-colors" title="X (Twitter)">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            </a>
            <a href="https://t.me/talos_agent" target="_blank" className="text-gray-500 hover:text-white transition-colors" title="Telegram">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
            </a>
            <Link href="/about" className="text-gray-500 hover:text-white transition-colors text-sm">
              About
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
