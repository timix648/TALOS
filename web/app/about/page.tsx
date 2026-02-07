"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-gray-950/80 border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl overflow-hidden">
              <Image src="/talos-logo.png" alt="TALOS" width={40} height={40} className="w-full h-full object-cover" />
            </div>
            <span className="text-xl font-bold">TALOS</span>
          </Link>
          <Link href="/" className="text-gray-400 hover:text-white transition-colors text-sm">
            Back to Home
          </Link>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-32 pb-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl sm:text-5xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400">
            About TALOS
          </h1>
          
          <p className="text-xl text-gray-300 mb-12">
            An autonomous CI/CD repair agent powered by Gemini 3.
          </p>

          <section className="space-y-12">

            <div>
              <h2 className="text-2xl font-bold mb-4 text-cyan-400">What is TALOS?</h2>
              <p className="text-gray-400 leading-relaxed">
                TALOS is an AI-powered DevOps agent that automatically detects and fixes CI/CD pipeline failures. 
                When your builds break, TALOS analyzes the error logs, identifies the root cause, generates a fix, 
                verifies it in an isolated sandbox, and opens a Pull Request - all without human intervention.
              </p>
            </div>

            <div>
              <h2 className="text-2xl font-bold mb-4 text-cyan-400">How It Works</h2>
              <div className="space-y-4">
                {[
                  { step: "01", title: "Detect", desc: "TALOS monitors your GitHub repositories via webhooks. When a CI/CD workflow fails, it captures the error logs and full context." },
                  { step: "02", title: "Analyze", desc: "Using Gemini 3, TALOS parses stack traces, builds dependency graphs, and identifies the root cause file responsible for the failure." },
                  { step: "03", title: "Fix", desc: "TALOS generates fixes in an isolated E2B sandbox, runs your test suite to verify the fix works, then opens a Pull Request for review." },
                  { step: "04", title: "Verify", desc: "Visual Cortex captures screenshots of the running application and uses AI vision to detect UI regressions before submitting the fix." },
                ].map((item) => (
                  <div key={item.title} className="flex gap-4 p-4 bg-gray-900/50 rounded-lg border border-gray-800">
                    <span className="text-2xl font-bold text-cyan-500/40 font-mono">{item.step}</span>
                    <div>
                      <h3 className="font-bold text-white">{item.title}</h3>
                      <p className="text-gray-400 text-sm">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

    
            <div>
              <h2 className="text-2xl font-bold mb-4 text-cyan-400">Tech Stack</h2>
              <div className="flex flex-wrap gap-3">
                {[
                  "Gemini 3",
                  "FastAPI",
                  "E2B Sandbox",
                  "Next.js 15",
                  "GitHub Apps",
                  "Supabase",
                  "Playwright",
                  "Python",
                  "TypeScript",
                ].map((tech) => (
                  <span key={tech} className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm">
                    {tech}
                  </span>
                ))}
              </div>
            </div>

           
            <div>
              <h2 className="text-2xl font-bold mb-4 text-cyan-400">Connect</h2>
              <div className="flex gap-4">
                <a 
                  href="https://github.com/timix648/TALOS" 
                  target="_blank"
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                  GitHub
                </a>
                <a 
                  href="https://x.com/0xGenZero" 
                  target="_blank"
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                  X (Twitter)
                </a>
                <a 
                  href="https://t.me/oxgenzero" 
                  target="_blank"
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
                  Telegram
                </a>
              </div>
            </div>
          </section>

         
          <div className="mt-16">
            <Link 
              href="/"
              className="text-gray-500 hover:text-white transition-colors"
            >
              ← Back to Home
            </Link>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
