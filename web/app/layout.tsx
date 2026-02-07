import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TALOS | Self-Healing DevOps Agent",
  description: "Autonomous CI/CD repair powered by Gemini 3. TALOS watches your GitHub repositories and automatically fixes build failures.",
  keywords: ["DevOps", "CI/CD", "GitHub", "Automation", "AI", "Gemini", "Self-Healing"],
  authors: [{ name: "TALOS Team" }],
  icons: {
    icon: "/talos-logo.png",
    apple: "/talos-logo.png",
  },
  openGraph: {
    title: "TALOS | Self-Healing DevOps Agent",
    description: "Autonomous CI/CD repair powered by Gemini 3",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body 
        className="font-sans antialiased" 
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}