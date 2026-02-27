import Image from "next/image";
import IntakeWizard from "./components/IntakeWizard";

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black font-sans selection:bg-indigo-500/30">
      <main className="flex flex-col items-center justify-start w-full px-4 sm:px-6 lg:px-8 pt-20 pb-32">
        {/* Header / Hero Section */}
        <div className="text-center max-w-3xl mb-16 space-y-4 animate-in fade-in slide-in-from-top-6 duration-700">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 text-sm font-semibold tracking-wide border border-indigo-200 dark:border-indigo-500/20 mb-4">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            <span>Permit Pulse — Toronto Edition</span>
          </div>

          <h1 className="text-5xl sm:text-7xl font-extrabold text-zinc-900 dark:text-zinc-50 tracking-tighter">
            Build <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Smarter</span>, Not Harder.
          </h1>

          <p className="text-xl text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            AI-powered response generation for Garden and Laneway Suite permit corrections. Verify your property below to start the <span className="font-semibold text-zinc-800 dark:text-zinc-200">5-minute</span> automated review.
          </p>
        </div>

        {/* Wizard Container */}
        <div className="w-full relative z-10">
          <div className="absolute inset-0 max-w-4xl mx-auto -z-10 bg-gradient-to-tr from-indigo-500/20 to-blue-500/20 blur-[120px] rounded-full translate-y-10" />
          <IntakeWizard />
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full text-center py-6 border-t border-zinc-200 dark:border-zinc-800 text-sm text-zinc-500 bg-white/50 dark:bg-zinc-950/50 backdrop-blur-md">
        Powered by CrossBeam AI. By proceeding, you agree to our Professional Liability terms.
      </footer>
    </div>
  );
}
