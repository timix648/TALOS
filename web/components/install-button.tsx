"use client";

import { motion } from "framer-motion";
import { useState } from "react";

interface InstallButtonProps {
  githubAppUrl?: string;
  variant?: "primary" | "secondary";
  size?: "sm" | "md" | "lg";
}

export default function InstallButton({ 
  githubAppUrl = "https://github.com/apps/talos-healer/installations/new",
  variant = "primary",
  size = "md"
}: InstallButtonProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = () => {
    setIsLoading(true);
    // Redirect to GitHub App installation
    window.location.href = githubAppUrl;
  };

  const sizeClasses = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg",
  };

  const variantClasses = {
    primary: "bg-gradient-to-r from-cyan-500 to-purple-600 text-white",
    secondary: "bg-gray-800 border border-gray-700 text-white hover:bg-gray-700",
  };

  return (
    <motion.button
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      disabled={isLoading}
      className={`
        relative overflow-hidden rounded-xl font-bold 
        transition-all duration-300 
        ${sizeClasses[size]} 
        ${variantClasses[variant]}
        ${isLoading ? "opacity-70 cursor-wait" : "hover:opacity-90"}
      `}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Shine effect */}
      {variant === "primary" && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
          initial={{ x: "-100%" }}
          animate={{ x: isHovered ? "100%" : "-100%" }}
          transition={{ duration: 0.6 }}
        />
      )}

      {/* Content */}
      <span className="relative flex items-center justify-center gap-2">
        {isLoading ? (
          <>
            <motion.div
              className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            />
            <span>Connecting...</span>
          </>
        ) : (
          <>
            <span className="text-xl">🔗</span>
            <span>Authorize TALOS for Your Repos</span>
          </>
        )}
      </span>

      {/* Glow effect */}
      {variant === "primary" && isHovered && (
        <motion.div
          className="absolute -inset-1 bg-gradient-to-r from-cyan-500/50 to-purple-600/50 rounded-xl blur-lg -z-10"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        />
      )}
    </motion.button>
  );
}

// Compact version for nav
export function InstallButtonCompact({ 
  githubAppUrl = "https://github.com/apps/talos-healer/installations/new" 
}) {
  return (
    <motion.a
      href={githubAppUrl}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg text-sm font-medium text-white hover:opacity-90 transition-opacity"
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <span>🧬</span>
      <span>Install</span>
    </motion.a>
  );
}
