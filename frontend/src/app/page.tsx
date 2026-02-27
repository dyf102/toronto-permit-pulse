"use client";

import React, { useState } from "react";
import IntakeWizard from "./components/IntakeWizard";
import ResultsDashboard from "./components/ResultsDashboard";

type AppView = "intake" | "results";

export default function Home() {
  const [view, setView] = useState<AppView>("intake");
  const [pipelineResult, setPipelineResult] = useState<any>(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/40 dark:from-zinc-950 dark:via-zinc-900 dark:to-zinc-950">
      {/* Navigation Bar */}
      <nav className="sticky top-0 z-50 bg-white/70 dark:bg-zinc-900/70 backdrop-blur-xl border-b border-zinc-200/50 dark:border-zinc-800/50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-zinc-900 dark:text-white tracking-tight">
                PermitPulse
              </h1>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 -mt-0.5">
                Toronto Permit Assistant
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {view === "results" && (
              <button
                onClick={() => {
                  setView("intake");
                  setPipelineResult(null);
                }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              >
                ← New Analysis
              </button>
            )}
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 rounded-lg text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/30 transition-colors"
            >
              API Docs
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-12">
        {view === "intake" && (
          <div className="space-y-8">
            {/* Hero Text */}
            <div className="text-center max-w-2xl mx-auto mb-4">
              <h2 className="text-4xl md:text-5xl font-extrabold text-zinc-900 dark:text-white tracking-tight leading-tight">
                AI-Powered Permit
                <span className="bg-gradient-to-r from-indigo-500 to-blue-600 bg-clip-text text-transparent">
                  {" "}
                  Correction Response
                </span>
              </h2>
              <p className="mt-4 text-lg text-zinc-600 dark:text-zinc-300 leading-relaxed">
                Upload your Examiner&apos;s Notice and get citation-backed
                correction responses drafted by specialist AI agents — in
                minutes, not weeks.
              </p>
            </div>

            <IntakeWizard
              onPipelineComplete={(result: any) => {
                setPipelineResult(result);
                setView("results");
              }}
            />
          </div>
        )}

        {view === "results" && pipelineResult && (
          <div className="space-y-6">
            <ResultsDashboard data={pipelineResult} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-200/50 dark:border-zinc-800/50 mt-24 py-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-xs text-zinc-400 dark:text-zinc-500">
          <p>
            PermitPulse Toronto © 2026 · AI-generated responses require
            professional review before submission.
          </p>
          <p className="mt-1">
            Not affiliated with the City of Toronto. For informational purposes
            only.
          </p>
        </div>
      </footer>
    </div>
  );
}
