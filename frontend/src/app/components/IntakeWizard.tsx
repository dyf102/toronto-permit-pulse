"use client";

import React, { useState } from "react";

export default function IntakeWizard() {
  const [step, setStep] = useState(1);
  const [address, setAddress] = useState("");
  const [suiteType, setSuiteType] = useState<"garden" | "laneway" | "">("");
  const [lanewayAbutment, setLanewayAbutment] = useState("");
  const [preApprovedPlan, setPreApprovedPlan] = useState("");

  const legacyMunicipalities = [
    "etobicoke",
    "north york",
    "scarborough",
    "york",
    "east york",
  ];
  const isLegacy = legacyMunicipalities.some((m) =>
    address.toLowerCase().includes(m)
  );

  const nextStep = () => {
    if (step === 1 && isLegacy) return;
    setStep((prev) => prev + 1);
  };

  const prevStep = () => setStep((prev) => prev - 1);

  return (
    <div className="w-full max-w-2xl mx-auto rounded-2xl shadow-2xl bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-zinc-200 dark:border-zinc-800 overflow-hidden transition-all duration-300">
      <div className="p-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between mb-2 text-sm font-semibold tracking-wider text-zinc-500 dark:text-zinc-400">
            <span>Intake</span>
            <span>Suite Type</span>
            <span>Details</span>
          </div>
          <div className="h-2 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden flex">
            <div
              className={`h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-500 ease-in-out ${
                step === 1 ? "w-1/3" : step === 2 ? "w-2/3" : "w-full"
              }`}
            />
          </div>
        </div>

        {/* Step 1: Address Intake */}
        {step === 1 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
              Property Details
            </h2>
            <p className="text-zinc-600 dark:text-zinc-300 text-lg">
              Enter the full property address in Toronto to verify eligibility.
            </p>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                Property Address
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                placeholder="e.g., 123 Spadina Ave, Toronto"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </div>

            {isLegacy && (
              <div className="p-4 rounded-lg bg-orange-50 border border-orange-200 dark:bg-orange-950/30 dark:border-orange-900/50 flex items-start space-x-3">
                <svg className="w-6 h-6 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                <div>
                  <h4 className="font-semibold text-orange-800 dark:text-orange-300">Manual Validation Required</h4>
                  <p className="text-orange-700 dark:text-orange-400 text-sm mt-1">
                    This property falls under a former municipal zoning by-law that is not supported by our automated compliance MVP. Please contact Toronto Building at <strong>416-397-5330</strong>.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Suite Type */}
        {step === 2 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
              Suite Type
            </h2>
            <p className="text-zinc-600 dark:text-zinc-300 text-lg">
              Are you building a Garden Suite or Laneway Suite?
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => setSuiteType("garden")}
                className={`p-6 rounded-xl border-2 text-left transition-all duration-200 ${
                  suiteType === "garden"
                    ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 ring-4 ring-indigo-500/20"
                    : "border-zinc-200 dark:border-zinc-700 hover:border-indigo-300 hover:bg-zinc-50 dark:hover:bg-zinc-800"
                }`}
              >
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-2xl">🏡</span>
                  <h3 className="font-semibold text-xl text-zinc-900 dark:text-white">Garden Suite</h3>
                </div>
                <p className="text-zinc-500 dark:text-zinc-400 text-sm">
                  Ancillary building abutting side or rear lot lines, but NOT a public laneway.
                </p>
              </button>

              <button
                onClick={() => setSuiteType("laneway")}
                className={`p-6 rounded-xl border-2 text-left transition-all duration-200 ${
                  suiteType === "laneway"
                    ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 ring-4 ring-indigo-500/20"
                    : "border-zinc-200 dark:border-zinc-700 hover:border-indigo-300 hover:bg-zinc-50 dark:hover:bg-zinc-800"
                }`}
              >
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-2xl">🛣️</span>
                  <h3 className="font-semibold text-xl text-zinc-900 dark:text-white">Laneway Suite</h3>
                </div>
                <p className="text-zinc-500 dark:text-zinc-400 text-sm">
                  Ancillary building abutting a public laneway at the side or rear.
                </p>
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Specific Details */}
        {step === 3 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
              Additional Requirements
            </h2>
            <p className="text-zinc-600 dark:text-zinc-300 text-lg">
              Just a few more specifics to help our AI analyze the plans correctly.
            </p>

            {suiteType === "laneway" && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                  Laneway Abutment Length (metres)
                </label>
                <input
                  type="number"
                  step="0.01"
                  className="w-full px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                  placeholder="e.g., 5.5"
                  value={lanewayAbutment}
                  onChange={(e) => setLanewayAbutment(e.target.value)}
                />
                <p className="text-xs text-zinc-500 mt-1">
                  Required to determine maximum permitted dimensions under Section 150.8.60.
                </p>
              </div>
            )}

            <div className="space-y-2">
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                Pre-approved Plan Number (Optional)
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                placeholder="e.g., PP-2024-001"
                value={preApprovedPlan}
                onChange={(e) => setPreApprovedPlan(e.target.value)}
              />
            </div>
          </div>
        )}
      </div>

      {/* Navigation Footer */}
      <div className="px-8 py-5 bg-zinc-50 dark:bg-zinc-950/50 border-t border-zinc-200 dark:border-zinc-800 flex justify-between items-center rounded-b-2xl">
        {step > 1 ? (
          <button
            onClick={prevStep}
            className="px-6 py-2.5 rounded-lg text-sm font-semibold text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors"
          >
            Back
          </button>
        ) : (
          <div /> // Spacer
        )}
        
        {step < 3 ? (
          <button
            onClick={nextStep}
            disabled={!address || isLegacy || (step === 2 && !suiteType)}
            className="px-6 py-2.5 rounded-lg text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
          >
            Next Step
          </button>
        ) : (
          <button
            onClick={() => alert("Moving to Uploads pipeline...")}
            className="px-6 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Proceed to Uploads
          </button>
        )}
      </div>
    </div>
  );
}
