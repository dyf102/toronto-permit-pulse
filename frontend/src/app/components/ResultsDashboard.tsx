"use client";

import React from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Citation {
    bylaw: string;
    section: string;
    version: string;
}

interface DeficiencyResponse {
    draft_text: string;
    resolution_status: string;
    citations: Citation[];
    variance_magnitude: string | null;
    agent_reasoning: string;
}

interface DeficiencyResult {
    deficiency: {
        category: string;
        raw_notice_text: string;
        extracted_action: string;
        agent_confidence: number;
    };
    response: DeficiencyResponse | null;
    agent: string;
    error?: string;
}

interface PipelineResult {
    session_id: string;
    suite_type: string;
    property_address: string;
    summary: {
        total_deficiencies: number;
        processed: number;
        unhandled: number;
        by_category: Record<string, number>;
    };
    results: DeficiencyResult[];
    unhandled: { deficiency: { category: string; raw_notice_text: string }; reason: string }[];
    status: string;
}

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
    RESOLVED: {
        bg: "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800",
        text: "text-emerald-700 dark:text-emerald-300",
        label: "✓ Resolved",
    },
    DRAWING_REVISION_NEEDED: {
        bg: "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800",
        text: "text-amber-700 dark:text-amber-300",
        label: "✏️ Drawing Revision",
    },
    VARIANCE_REQUIRED: {
        bg: "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800",
        text: "text-red-700 dark:text-red-300",
        label: "⚠️ Variance Required",
    },
    LDA_REQUIRED: {
        bg: "bg-purple-50 dark:bg-purple-950/30 border-purple-200 dark:border-purple-800",
        text: "text-purple-700 dark:text-purple-300",
        label: "📋 LDA Required",
    },
    OUT_OF_SCOPE: {
        bg: "bg-zinc-50 dark:bg-zinc-900/30 border-zinc-200 dark:border-zinc-700",
        text: "text-zinc-600 dark:text-zinc-400",
        label: "— Out of Scope",
    },
};

const CATEGORY_ICONS: Record<string, string> = {
    ZONING: "🏗️",
    OBC: "📐",
    FIRE_ACCESS: "🔥",
    TREE_PROTECTION: "🌳",
    LANDSCAPING: "🌿",
    SERVICING: "🔧",
    OTHER: "📄",
};

export default function ResultsDashboard({ data }: { data: PipelineResult }) {
    const [expandedIdx, setExpandedIdx] = React.useState<number | null>(null);
    const [isDownloading, setIsDownloading] = React.useState(false);
    const [downloadError, setDownloadError] = React.useState<string | null>(null);
    const [showDisclaimer, setShowDisclaimer] = React.useState(false);
    const [disclaimerAcknowledged, setDisclaimerAcknowledged] = React.useState(false);

    const resolvedCount = data.results.filter(
        (r) => r.response?.resolution_status === "RESOLVED"
    ).length;
    const varianceCount = data.results.filter(
        (r) => r.response?.resolution_status === "VARIANCE_REQUIRED"
    ).length;
    const revisionCount = data.results.filter(
        (r) => r.response?.resolution_status === "DRAWING_REVISION_NEEDED"
    ).length;

    const handleDownloadClick = () => {
        if (disclaimerAcknowledged) {
            handleDownloadPDF();
        } else {
            setShowDisclaimer(true);
        }
    };

    const handleDisclaimerAccept = () => {
        setDisclaimerAcknowledged(true);
        setShowDisclaimer(false);
        handleDownloadPDF();
    };

    const handleDownloadPDF = async () => {
        setIsDownloading(true);
        setDownloadError(null);
        try {
            const res = await fetch(`${API_URL}/api/v1/export/pdf`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: "PDF generation failed" }));
                throw new Error(err.detail || "Export failed");
            }
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            const addrSlug = data.property_address
                .replace(/,/g, "")
                .replace(/\s+/g, "_")
                .toLowerCase()
                .slice(0, 40);
            link.download = `resubmission_package_${addrSlug}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } catch (err: unknown) {
            setDownloadError(err instanceof Error ? err.message : "Download failed");
        } finally {
            setIsDownloading(false);
        }
    };

    return (
        <div className="w-full max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="rounded-2xl shadow-2xl bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-zinc-200 dark:border-zinc-800 p-8">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h1 className="text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
                            Analysis Complete
                        </h1>
                        <p className="text-zinc-500 dark:text-zinc-400 mt-1">
                            {data.property_address} · {data.suite_type.replace("_", " ")} Suite
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            id="download-pdf-btn"
                            onClick={handleDownloadClick}
                            disabled={isDownloading}
                            className="px-5 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            {isDownloading ? (
                                <>
                                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Generating PDF…
                                </>
                            ) : (
                                <>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    Download PDF
                                </>
                            )}
                        </button>
                        <div className="px-4 py-2 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 text-sm font-semibold">
                            {data.status}
                        </div>
                    </div>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                    <StatCard
                        label="Total Issues"
                        value={data.summary.total_deficiencies}
                        color="indigo"
                    />
                    <StatCard label="Resolved" value={resolvedCount} color="emerald" />
                    <StatCard label="Need Revision" value={revisionCount} color="amber" />
                    <StatCard label="Variance" value={varianceCount} color="red" />
                </div>

                {/* Download Error Banner */}
                {downloadError && (
                    <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 dark:bg-red-950/30 dark:border-red-900/50 text-red-700 dark:text-red-300 text-sm">
                        <strong>Export Error:</strong> {downloadError}
                    </div>
                )}

                {/* Category Breakdown */}
                <div className="mt-6 flex flex-wrap gap-2">
                    {Object.entries(data.summary.by_category).map(([cat, count]) => (
                        <span
                            key={cat}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 text-sm font-medium"
                        >
                            {CATEGORY_ICONS[cat] || "📄"} {cat.replace("_", " ")}
                            <span className="ml-1 text-xs bg-zinc-200 dark:bg-zinc-700 px-1.5 py-0.5 rounded-full">
                                {count}
                            </span>
                        </span>
                    ))}
                </div>
            </div>

            {/* Deficiency Cards */}
            {data.results.map((result, idx) => {
                const status = result.response?.resolution_status || "OUT_OF_SCOPE";
                const style = STATUS_STYLES[status] || STATUS_STYLES.OUT_OF_SCOPE;
                const isExpanded = expandedIdx === idx;

                return (
                    <div
                        key={idx}
                        className={`rounded-xl border shadow-sm transition-all duration-300 ${style.bg} overflow-hidden`}
                    >
                        {/* Card Header */}
                        <button
                            onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                            className="w-full px-6 py-5 flex items-start justify-between text-left hover:opacity-90 transition-opacity"
                        >
                            <div className="flex items-start gap-3 flex-1">
                                <span className="text-2xl mt-0.5">
                                    {CATEGORY_ICONS[result.deficiency.category] || "📄"}
                                </span>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`text-xs font-bold uppercase tracking-wider ${style.text}`}>
                                            {result.deficiency.category.replace("_", " ")}
                                        </span>
                                        <span className="text-zinc-400 dark:text-zinc-600">·</span>
                                        <span className="text-xs text-zinc-500 dark:text-zinc-400">
                                            {result.agent}
                                        </span>
                                    </div>
                                    <p className="text-sm text-zinc-800 dark:text-zinc-200 line-clamp-2">
                                        {result.deficiency.extracted_action}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 ml-4 flex-shrink-0">
                                <span
                                    className={`px-3 py-1 rounded-full text-xs font-semibold ${style.text} ${style.bg} border`}
                                >
                                    {style.label}
                                </span>
                                <svg
                                    className={`w-5 h-5 text-zinc-400 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""
                                        }`}
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="2"
                                        d="M19 9l-7 7-7-7"
                                    />
                                </svg>
                            </div>
                        </button>

                        {/* Expanded Details */}
                        {isExpanded && result.response && (
                            <div className="px-6 pb-6 space-y-4 border-t border-zinc-200/50 dark:border-zinc-700/50">
                                {/* Original Notice Text */}
                                <div className="mt-4">
                                    <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 mb-2">
                                        Original Notice Text
                                    </h4>
                                    <p className="text-sm text-zinc-600 dark:text-zinc-300 bg-white/50 dark:bg-zinc-950/50 rounded-lg p-3 border border-zinc-200/50 dark:border-zinc-700/50 italic">
                                        &ldquo;{result.deficiency.raw_notice_text}&rdquo;
                                    </p>
                                </div>

                                {/* Draft Response */}
                                <div>
                                    <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 mb-2">
                                        Draft Response
                                    </h4>
                                    <div className="text-sm text-zinc-800 dark:text-zinc-200 bg-white/50 dark:bg-zinc-950/50 rounded-lg p-4 border border-zinc-200/50 dark:border-zinc-700/50 leading-relaxed">
                                        {result.response.draft_text}
                                    </div>
                                </div>

                                {/* Citations */}
                                {result.response.citations.length > 0 && (
                                    <div>
                                        <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 mb-2">
                                            Citations
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {result.response.citations.map((cite, i) => (
                                                <span
                                                    key={i}
                                                    className="inline-flex items-center px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 text-xs font-mono"
                                                >
                                                    {cite.bylaw} §{cite.section}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Variance Magnitude */}
                                {result.response.variance_magnitude && (
                                    <div className="p-3 rounded-lg bg-red-50/50 dark:bg-red-950/20 border border-red-200/50 dark:border-red-800/50">
                                        <span className="text-xs font-bold uppercase tracking-wider text-red-600 dark:text-red-400">
                                            Variance Magnitude:{" "}
                                        </span>
                                        <span className="text-sm text-red-700 dark:text-red-300">
                                            {result.response.variance_magnitude}
                                        </span>
                                    </div>
                                )}

                                {/* Agent Reasoning */}
                                <details className="group">
                                    <summary className="text-xs font-bold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 cursor-pointer hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
                                        Show Agent Reasoning ▸
                                    </summary>
                                    <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-100/50 dark:bg-zinc-800/50 rounded-lg p-3">
                                        {result.response.agent_reasoning}
                                    </p>
                                </details>

                                {/* Confidence Score */}
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-zinc-400">Confidence:</span>
                                    <div className="flex-1 h-1.5 bg-zinc-200 dark:bg-zinc-700 rounded-full overflow-hidden max-w-[120px]">
                                        <div
                                            className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full"
                                            style={{
                                                width: `${result.deficiency.agent_confidence * 100}%`,
                                            }}
                                        />
                                    </div>
                                    <span className="text-xs text-zinc-500 font-mono">
                                        {(result.deficiency.agent_confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                            </div>
                        )}

                        {/* Error State */}
                        {isExpanded && result.error && (
                            <div className="px-6 pb-6 border-t border-zinc-200/50 dark:border-zinc-700/50">
                                <div className="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
                                    <strong>Error:</strong> {result.error}
                                </div>
                            </div>
                        )}
                    </div>
                );
            })}

            {/* Unhandled Items */}
            {data.unhandled.length > 0 && (
                <div className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-900/50 p-6">
                    <h3 className="text-lg font-semibold text-zinc-700 dark:text-zinc-300 mb-3">
                        Unhandled Items ({data.unhandled.length})
                    </h3>
                    {data.unhandled.map((item, idx) => (
                        <div
                            key={idx}
                            className="p-3 mb-2 rounded-lg bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-sm"
                        >
                            <p className="text-zinc-600 dark:text-zinc-300">
                                {item.deficiency.raw_notice_text}
                            </p>
                            <p className="text-xs text-zinc-400 mt-1">{item.reason}</p>
                        </div>
                    ))}
                </div>
            )}
            {/* Professional Liability Disclaimer Modal */}
            {showDisclaimer && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-[fadeIn_0.2s_ease-out]"
                        onClick={() => setShowDisclaimer(false)}
                    />
                    {/* Modal */}
                    <div className="relative w-full max-w-lg bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 overflow-hidden animate-[slideUp_0.3s_ease-out]">
                        {/* Red header bar */}
                        <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
                            <div className="flex items-center gap-3">
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                </svg>
                                <h3 className="text-lg font-bold text-white">
                                    Professional Liability Disclaimer
                                </h3>
                            </div>
                        </div>
                        {/* Content */}
                        <div className="px-6 py-5 max-h-[60vh] overflow-y-auto space-y-4 text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed">
                            <p>
                                This document was generated by <strong>PermitPulse Toronto</strong>,
                                an AI-powered permit correction response system. The responses,
                                citations, and analysis contained herein were produced by artificial
                                intelligence and have <strong className="text-red-600 dark:text-red-400">NOT</strong> been
                                reviewed by a licensed architect, professional engineer, or Ontario
                                Land Surveyor.
                            </p>
                            <p>
                                This document is provided for <strong>INFORMATIONAL PURPOSES ONLY</strong> and
                                does not constitute professional advice. Before submitting any response
                                to the City of Toronto Plans Examination Branch, the applicant must
                                have all proposed revisions reviewed and stamped by the appropriate
                                licensed professional(s) as required by:
                            </p>
                            <ul className="list-disc pl-5 space-y-1">
                                <li>Ontario Building Code Act, 1992 (S.O. 1992, c. 23)</li>
                                <li>Professional Engineers Act (R.S.O. 1990, c. P.28)</li>
                                <li>Architects Act (R.S.O. 1990, c. A.26)</li>
                                <li>Ontario Land Surveyors Act (R.S.O. 1990, c. O.12)</li>
                            </ul>
                            <p className="text-xs text-zinc-500 dark:text-zinc-500">
                                PermitPulse Toronto, its developers, and affiliates accept no
                                liability for any decisions made or actions taken based on the
                                content of this document. Regulatory requirements are subject to
                                change; always verify against the current applicable by-laws and codes.
                            </p>
                        </div>
                        {/* Actions */}
                        <div className="px-6 py-4 bg-zinc-50 dark:bg-zinc-800/50 border-t border-zinc-200 dark:border-zinc-700 flex items-center justify-end gap-3">
                            <button
                                onClick={() => setShowDisclaimer(false)}
                                className="px-4 py-2 rounded-lg text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                id="accept-disclaimer-btn"
                                onClick={handleDisclaimerAccept}
                                className="px-5 py-2.5 rounded-lg text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700 transition-all shadow-md flex items-center gap-2"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                </svg>
                                I Acknowledge — Download PDF
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function StatCard({
    label,
    value,
    color,
}: {
    label: string;
    value: number;
    color: string;
}) {
    const colorMap: Record<string, string> = {
        indigo: "from-indigo-500 to-indigo-600",
        emerald: "from-emerald-500 to-emerald-600",
        amber: "from-amber-500 to-amber-600",
        red: "from-red-500 to-red-600",
    };

    return (
        <div className="rounded-xl bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 p-4 text-center">
            <div
                className={`text-3xl font-extrabold bg-gradient-to-br ${colorMap[color] || colorMap.indigo
                    } bg-clip-text text-transparent`}
            >
                {value}
            </div>
            <div className="text-xs font-medium text-zinc-500 dark:text-zinc-400 mt-1 uppercase tracking-wider">
                {label}
            </div>
        </div>
    );
}
