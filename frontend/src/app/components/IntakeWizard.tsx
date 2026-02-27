"use client";

import React, { useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type WizardStep = 1 | 2 | 3 | 4;

const PIPELINE_STAGES = [
    { key: "upload", label: "Uploading PDF" },
    { key: "parse", label: "Parsing Notice (Gemini Vision)" },
    { key: "analyze", label: "Analyzing Deficiencies" },
    { key: "draft", label: "Drafting Responses" },
];

interface IntakeWizardProps {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onPipelineComplete?: (result: any) => void;
}

export default function IntakeWizard({ onPipelineComplete }: IntakeWizardProps) {
    const [step, setStep] = useState<WizardStep>(1);
    const [address, setAddress] = useState("");
    const [suiteType, setSuiteType] = useState<"GARDEN" | "LANEWAY" | "">("");
    const [lanewayAbutment, setLanewayAbutment] = useState("");
    const [preApprovedPlan, setPreApprovedPlan] = useState("");

    // Session & Upload state
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploadStatus, setUploadStatus] = useState<string | null>(null);
    const [activeStage, setActiveStage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

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
        setStep((prev) => (prev + 1) as WizardStep);
    };

    const prevStep = () => setStep((prev) => (prev - 1) as WizardStep);

    const handleCreateSession = useCallback(async () => {
        setIsSubmitting(true);
        setError(null);
        try {
            const res = await fetch(`${API_URL}/api/v1/sessions`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    property_address: address,
                    suite_type: suiteType,
                    laneway_abutment_length: lanewayAbutment
                        ? parseFloat(lanewayAbutment)
                        : null,
                    pre_approved_plan_number: preApprovedPlan || null,
                }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to create session");
            }

            const data: { session_id: string; status: string; upload_url: string } = await res.json();
            setSessionId(data.session_id);
            setStep(4);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "An error occurred");
        } finally {
            setIsSubmitting(false);
        }
    }, [address, suiteType, lanewayAbutment, preApprovedPlan]);

    const handleRunPipeline = useCallback(async () => {
        if (!uploadFile || !suiteType) return;
        setIsSubmitting(true);
        setError(null);

        try {
            setActiveStage("upload");
            const formData = new FormData();
            formData.append("file", uploadFile);
            formData.append("property_address", address);
            formData.append("suite_type", suiteType);
            if (lanewayAbutment) {
                formData.append("laneway_abutment_length", lanewayAbutment);
            }

            // Small delay to show upload stage
            await new Promise((r) => setTimeout(r, 400));
            setActiveStage("parse");

            const res = await fetch(`${API_URL}/api/v1/pipeline/run`, {
                method: "POST",
                body: formData,
            });

            setActiveStage("analyze");
            await new Promise((r) => setTimeout(r, 300));
            setActiveStage("draft");

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Pipeline failed");
            }

            const data = await res.json();
            setUploadStatus("complete");

            // Hand off to parent
            if (onPipelineComplete) {
                onPipelineComplete(data);
            }
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Pipeline failed");
            setActiveStage(null);
        } finally {
            setIsSubmitting(false);
        }
    }, [uploadFile, sessionId, address, suiteType, lanewayAbutment, onPipelineComplete]);

    return (
        <div className="w-full max-w-2xl mx-auto rounded-2xl shadow-2xl bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-zinc-200 dark:border-zinc-800 overflow-hidden transition-all duration-300">
            <div className="p-8">
                {/* Progress Bar */}
                <div className="mb-8">
                    <div className="flex justify-between mb-2 text-sm font-semibold tracking-wider text-zinc-500 dark:text-zinc-400">
                        <span>Intake</span>
                        <span>Suite Type</span>
                        <span>Details</span>
                        <span>Upload</span>
                    </div>
                    <div className="h-2 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden flex">
                        <div
                            className={`h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-500 ease-in-out ${step === 1
                                ? "w-1/4"
                                : step === 2
                                    ? "w-2/4"
                                    : step === 3
                                        ? "w-3/4"
                                        : "w-full"
                                }`}
                        />
                    </div>
                </div>

                {/* Error Banner */}
                {error && (
                    <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 dark:bg-red-950/30 dark:border-red-900/50 text-red-700 dark:text-red-300 text-sm">
                        <strong>Error:</strong> {error}
                    </div>
                )}

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
                                id="address-input"
                                type="text"
                                className="w-full px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                                placeholder="e.g., 123 Spadina Ave, Toronto"
                                value={address}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                    setAddress(e.target.value)
                                }
                            />
                        </div>

                        {isLegacy && (
                            <div className="p-4 rounded-lg bg-orange-50 border border-orange-200 dark:bg-orange-950/30 dark:border-orange-900/50 flex items-start space-x-3">
                                <svg
                                    className="w-6 h-6 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="2"
                                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                    />
                                </svg>
                                <div>
                                    <h4 className="font-semibold text-orange-800 dark:text-orange-300">
                                        Manual Validation Required
                                    </h4>
                                    <p className="text-orange-700 dark:text-orange-400 text-sm mt-1">
                                        This property falls under a former municipal zoning by-law
                                        that is not supported by our automated compliance MVP.
                                        Please contact Toronto Building at{" "}
                                        <strong>416-397-5330</strong>.
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
                                id="garden-suite-btn"
                                onClick={() => setSuiteType("GARDEN")}
                                className={`p-6 rounded-xl border-2 text-left transition-all duration-200 ${suiteType === "GARDEN"
                                    ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 ring-4 ring-indigo-500/20"
                                    : "border-zinc-200 dark:border-zinc-700 hover:border-indigo-300 hover:bg-zinc-50 dark:hover:bg-zinc-800"
                                    }`}
                            >
                                <div className="flex items-center space-x-3 mb-2">
                                    <span className="text-2xl">🏡</span>
                                    <h3 className="font-semibold text-xl text-zinc-900 dark:text-white">
                                        Garden Suite
                                    </h3>
                                </div>
                                <p className="text-zinc-500 dark:text-zinc-400 text-sm">
                                    Ancillary building abutting side or rear lot lines, but NOT a
                                    public laneway.
                                </p>
                            </button>

                            <button
                                id="laneway-suite-btn"
                                onClick={() => setSuiteType("LANEWAY")}
                                className={`p-6 rounded-xl border-2 text-left transition-all duration-200 ${suiteType === "LANEWAY"
                                    ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 ring-4 ring-indigo-500/20"
                                    : "border-zinc-200 dark:border-zinc-700 hover:border-indigo-300 hover:bg-zinc-50 dark:hover:bg-zinc-800"
                                    }`}
                            >
                                <div className="flex items-center space-x-3 mb-2">
                                    <span className="text-2xl">🛣️</span>
                                    <h3 className="font-semibold text-xl text-zinc-900 dark:text-white">
                                        Laneway Suite
                                    </h3>
                                </div>
                                <p className="text-zinc-500 dark:text-zinc-400 text-sm">
                                    Ancillary building abutting a public laneway at the side or
                                    rear.
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
                            Just a few more specifics to help our AI analyze the plans
                            correctly.
                        </p>

                        {suiteType === "LANEWAY" && (
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                                    Laneway Abutment Length (metres)
                                </label>
                                <input
                                    id="abutment-input"
                                    type="number"
                                    step="0.01"
                                    className="w-full px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                                    placeholder="e.g., 5.5"
                                    value={lanewayAbutment}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                        setLanewayAbutment(e.target.value)
                                    }
                                />
                                <p className="text-xs text-zinc-500 mt-1">
                                    Required to determine maximum permitted dimensions under
                                    Section 150.8.60.
                                </p>
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                                Pre-approved Plan Number (Optional)
                            </label>
                            <input
                                id="plan-number-input"
                                type="text"
                                className="w-full px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                                placeholder="e.g., PP-2024-001"
                                value={preApprovedPlan}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                    setPreApprovedPlan(e.target.value)
                                }
                            />
                        </div>
                    </div>
                )}

                {/* Step 4: Upload */}
                {step === 4 && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <h2 className="text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
                            Upload Examiner&apos;s Notice
                        </h2>
                        <p className="text-zinc-600 dark:text-zinc-300 text-lg">
                            Upload the PDF of the Examiner&apos;s Notice you received from
                            Toronto Building.
                        </p>

                        {sessionId && (
                            <div className="p-3 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800 text-sm">
                                <span className="font-semibold text-indigo-700 dark:text-indigo-300">
                                    Session:
                                </span>{" "}
                                <code className="text-indigo-600 dark:text-indigo-400">
                                    {sessionId}
                                </code>
                            </div>
                        )}

                        <div className="space-y-4">
                            <label
                                htmlFor="pdf-upload"
                                className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed border-zinc-300 dark:border-zinc-700 rounded-xl cursor-pointer hover:border-indigo-400 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 transition-all"
                            >
                                <svg
                                    className="w-10 h-10 text-zinc-400 mb-2"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="1.5"
                                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                                    />
                                </svg>
                                <span className="text-sm text-zinc-600 dark:text-zinc-400">
                                    {uploadFile ? uploadFile.name : "Click to select PDF (max 250 MB)"}
                                </span>
                                <input
                                    id="pdf-upload"
                                    type="file"
                                    accept=".pdf"
                                    className="hidden"
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                                        if (e.target.files && e.target.files[0]) {
                                            setUploadFile(e.target.files[0]);
                                            setUploadStatus(null);
                                            setError(null);
                                        }
                                    }}
                                />
                            </label>

                            {uploadFile && !uploadStatus && (
                                <button
                                    id="upload-btn"
                                    onClick={handleRunPipeline}
                                    disabled={isSubmitting}
                                    className="w-full px-6 py-3 rounded-lg text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isSubmitting ? "Running Analysis..." : "Upload & Run AI Analysis"}
                                </button>
                            )}

                            {/* Pipeline progress indicator */}
                            {isSubmitting && activeStage && (
                                <div className="mt-4 space-y-2">
                                    {PIPELINE_STAGES.map((stage, i) => {
                                        const stageIdx = PIPELINE_STAGES.findIndex(s => s.key === activeStage);
                                        const isDone = i < stageIdx;
                                        const isActive = stage.key === activeStage;
                                        return (
                                            <div key={stage.key} className="flex items-center gap-3">
                                                <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300 ${isDone ? "bg-emerald-500" : isActive ? "bg-indigo-500 animate-pulse" : "bg-zinc-200 dark:bg-zinc-700"
                                                    }`}>
                                                    {isDone && (
                                                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                                                        </svg>
                                                    )}
                                                </div>
                                                <span className={`text-sm transition-colors duration-200 ${isDone ? "text-emerald-600 dark:text-emerald-400 line-through" :
                                                    isActive ? "text-indigo-600 dark:text-indigo-400 font-semibold" :
                                                        "text-zinc-400 dark:text-zinc-600"
                                                    }`}>
                                                    {stage.label}
                                                </span>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Navigation Footer */}
            <div className="px-8 py-5 bg-zinc-50 dark:bg-zinc-950/50 border-t border-zinc-200 dark:border-zinc-800 flex justify-between items-center rounded-b-2xl">
                {step > 1 && step < 4 ? (
                    <button
                        onClick={prevStep}
                        className="px-6 py-2.5 rounded-lg text-sm font-semibold text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors"
                    >
                        Back
                    </button>
                ) : (
                    <div />
                )}

                {step < 3 ? (
                    <button
                        id="next-step-btn"
                        onClick={nextStep}
                        disabled={!address || isLegacy || (step === 2 && !suiteType)}
                        className="px-6 py-2.5 rounded-lg text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                    >
                        Next Step
                    </button>
                ) : step === 3 ? (
                    <button
                        id="proceed-btn"
                        onClick={handleCreateSession}
                        disabled={isSubmitting}
                        className="px-6 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSubmitting ? (
                            <span className="flex items-center space-x-2">
                                <svg
                                    className="animate-spin h-4 w-4"
                                    viewBox="0 0 24 24"
                                >
                                    <circle
                                        className="opacity-25"
                                        cx="12"
                                        cy="12"
                                        r="10"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                        fill="none"
                                    />
                                    <path
                                        className="opacity-75"
                                        fill="currentColor"
                                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                                    />
                                </svg>
                                <span>Creating Session...</span>
                            </span>
                        ) : (
                            "Proceed to Uploads"
                        )}
                    </button>
                ) : null}
            </div>
        </div>
    );
}
