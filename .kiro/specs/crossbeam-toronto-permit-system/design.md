# System Design Document: CrossBeam Toronto Permit System

**Version:** 2.1 — Technical Integrity Update
**Date:** March 1, 2026

---

## 1. Introduction & Overview

CrossBeam Toronto is an AI-powered permit correction response system targeting Garden Suites and Laneway Suites in the City of Toronto. The system ingests user-uploaded architectural plans and Examiner's Notices, orchestrates a suite of specialized AI agents to evaluate regulatory compliance (Zoning By-law 569-2013, OBC, Municipal Code Chapter 813, etc.), asks clarifying questions when necessary, and generates a complete resubmission package with citation-backed responses.

This design document translates the product requirements (v2.0) into a technical system architecture, with emphasis on technical integrity, P.Eng.-level auditing, and robust regulatory cross-referencing.

### 1.1 Revision Notes

This revision (v2.1) addresses technical integrity and regulatory survival:

- **Model references updated:** Standardized on the Gemini 3 family (Gemini 3.1 Pro for auditing, Gemini 3 Flash for drafting). Added support for partner models (Claude Opus 4.6) via Vertex AI.
- **Logic Auditor integration:** Added a Reviewer Agent (Logic_Auditor) to the orchestration pipeline to perform automated P.Eng.-level peer review before finalization.
- **Recursive RAG context:** Implemented section-aware recursive retrieval to ensure parent/general by-law sections are always included in agent context.
- **Security hardening:** Integrated reCAPTCHA (production mode), strict file validation (10MB limit), and result caching.
- **Evaluation framework:** Formalized the `EvalPipeline` for benchmarking response quality against a P.Eng. "Gold Standard."

---

## 2. High-Level Architecture

The system follows a decoupled architecture designed for heavy asynchronous workloads and AI sandboxing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                          │
│              permit-pulse.ca — Vercel Edge Hosting                  │
│                                                                     │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐ │
│  │  Intake   │→│  Upload &    │→│  Analysis   │→│   Review &    │ │
│  │  Wizard   │  │  Ingestion   │  │  Dashboard  │  │   Download    │ │
│  └──────────┘  └──────┬───────┘  └──────┬─────┘  └──────────────┘ │
└──────────────────────┬────────────────┬─┘                          │
                       │                │     ▲  WebSocket/SSE       │
                       │  Pre-signed    │     │  (status + clarify)  │
                       │  URL upload    │     │                      │
                       ▼                ▼     │                      │
┌──────────────────────────────────────────────────────────────────┐ │
│              OBJECT STORAGE (S3 / GCS)                           │ │
│              250 MB PDF uploads, session artifacts                │ │
└──────────────────────┬───────────────────────────────────────────┘ │
                       │ Event trigger                               │
                       ▼                                              │
┌─────────────────────────────────────────────────────────────────────┐
│                  API GATEWAY & ORCHESTRATOR                         │
│              Python (FastAPI) — Cloud Run / ECS Fargate              │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              State Machine (PermitSession)                  │    │
│  │  INTAKE → UPLOADING → ANALYZING → CLARIFYING → COMPLETE    │    │
│  └────────────┬───────────────────────────────────────────────┘    │
│               │                                                     │
│  ┌────────────▼────────────────────────────────────────────────┐   │
│  │           AGENT EXECUTION GRAPH (Parallel where possible)    │   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │
│  │  │  Blueprint    │  │  Examiner    │  │  Zoning          │  │   │
│  │  │  Reader       │  │  Notice      │  │  Classifier      │  │   │
│  │  │  (Opus 4.6    │  │  Parser      │  │                  │  │   │
│  │  │   Vision)     │  │              │  │                  │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │   │
│  │         └────────┬────────┘                    │            │   │
│  │                  ▼                             │            │   │
│  │  ┌──────────────────────────────────┐         │            │   │
│  │  │       Suite Type Router          │◄────────┘            │   │
│  │  └──────────────┬───────────────────┘                      │   │
│  │     ┌───────────┼───────────┬───────────┬──────────┐       │   │
│  │     ▼           ▼           ▼           ▼          ▼       │   │
│  │  Footprint   Height &    Fire Access  Tree      Soft       │   │
│  │  Validator   Setback     Validator    Assessor  Landscape  │   │
│  │              Validators  (1.0m/0.9m)            Validator   │   │
│  │     │           │           │           │          │       │   │
│  │     └───────────┼───────────┼───────────┘          │       │   │
│  │                 ▼           │                      │       │   │
│  │           OBC Checker       │                      │       │   │
│  │           Servicing ◄───────┘                      │       │   │
│  │                 │                                  │       │   │
│  │                 └──────────┬────────────────────────┘       │   │
│  │                           ▼                                │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │           LOGIC AUDITOR (Peer Review Agent)          │  │   │
│  │  │           (Gemini 3.1 Pro P.Eng. Auditor)            │  │   │
│  │  └────────────────────────┬─────────────────────────────┘  │   │
│  │                           ▼                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │   │
│  │  │  Regulatory   │  │  Citation    │  │  Response        │ │   │
│  │  │  Updater      │  │  Generator   │  │  Drafter         │ │   │
│  │  │  (Web Search) │  │              │  │                  │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │           KNOWLEDGE BASE                                      │ │
│  │  Vector DB (pgvector / Qdrant) + Structured Document Store   │  │
│  │  Recursive context strategy (Parent-Child section linking)   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Component Summary

| Layer                      | Technology                                             | Responsibility                                                                                     |
| -------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Frontend                   | Next.js (React) + TypeScript, Vercel Edge              | Intake wizard, reCAPTCHA, live agent dashboard, response review, download                         |
| API Gateway & Orchestrator | Python (FastAPI), Cloud Run / ECS Fargate              | State machine, agent coordination, Audit Loop integration, result caching                          |
| AI Agent Sandboxes         | Containerized Google GenAI SDK instances               | specialized agents running in isolation with Quantitative Matrix enforcement                       |
| Vision Service             | Claude 4.6 (Vertex AI) / Gemini 3.1 Pro                | Reading architectural plans and Examiner's Notices with spatial reasoning                         |
| ETL Pipeline               | Celery / Prefect workers, event-driven via SQS/Pub-Sub | Section-aware regulatory knowledge updates, recursive parent-child linking                         |
| Knowledge Base             | pgvector (or managed Qdrant) + PostgreSQL              | versioned reference files with regex-based section hierarchy metadata                              |
| Object Storage             | S3 / GCS                                               | 250 MB PDF uploads, generated response packages, session artifacts                                 |
| Cache & Queue              | Redis + SQS/Pub-Sub                                    | Result caching (hashing address + PDF), low-latency state handling                                 |

---

## 3. Front-End Design & User Experience

CrossBeam Toronto is deployed as a standalone web product at **`https://permit-pulse.ca/`**, sharing a design system with the broader CrossBeam tool suite for consistent branding.

### 3.1 Core User Flows

**Flow 1 — Intake & Discovery**

A step-by-step wizard collecting property address, suite type (Garden or Laneway), laneway abutment confirmation, and optional pre-approved plan reference. The system provides immediate feedback on eligibility: if the address maps to a former municipal zoning by-law (Etobicoke, North York, Scarborough, York, or East York), the wizard displays a clear notice that automated compliance validation is not available in the MVP and directs the user to contact Toronto Building at 416-397-5330.

**Flow 2 — Document Ingestion**

Resumable, chunked drag-and-drop uploads using pre-signed URLs for direct-to-storage transfer. Two dedicated dropzones: one for Architectural Plans, one for the Examiner's Notice. Client-side validation enforces the 250 MB limit, reCAPTCHA verification, and standardized sheet sizes. A progress bar reflects upload status with automatic retry on network interruption.

**Flow 3 — Analysis & Orchestration**

Given the 5-minute SLA, a static spinner is insufficient. The UI renders an **Agent Execution Pipeline** — a live telemetry panel showing active agents and their progress. Example transitions:

> ✓ Blueprint Reader — extracted 18 pages, 47 dimensions identified  
> ● Footprint Validator — verifying By-law 569-2013, Section 150.8.60…  
> ● Logic Auditor — peer reviewing Footprint response (P.Eng. check)…
> ○ Fire Access Validator — queued  

Each agent transitions from queued → active → complete (or → clarification needed), giving the user confidence that work is progressing.

---

## 4. Backend Orchestration & AI Agents

### 4.2 Orchestration Workflow

The orchestrator operates as a state machine on the `PermitSession` entity:

```
INTAKE → UPLOADING → PARSING → ANALYZING → [AUDITING ↔ REVISING] → DRAFTING → COMPLETE
                                                                                    ↓
                                                                                  ERROR
```

**Step 3 — Parallel Agent Execution & Technical Rigor**

Agents execute in a parallel dependency graph. All measurement-based validators are now mandated to produce:
1.  **Quantitative Data:** Specific numerical evidence (e.g., "Reduced from 48.5m² to 44.2m²").
2.  **Technical Compliance Matrix:** A comparison table (Required vs. Proposed vs. Result).
3.  **Dual-Constraint Logic:** Explicit checks for "lesser of" or "greater of" rules (e.g., the 45.0m² cap).

**Step 4 — Automated Peer Review (The Auditor)**

Once a specialized agent generates a draft, the **Logic Auditor** (Gemini 3.1 Pro) performs a peer review. It checks for:
- Missing quantitative data.
- Fabrication of by-law citations.
- Failure to meet parent-level regulatory triggers (e.g., the 45sqm footprint override).
If the audit fails, the response is routed back for revision with specific P.Eng. feedback before the user sees it.

**Step 5 — Recursive Knowledge Retrieval (RAG)**

Retrieval is now section-aware. When a subsection is found (e.g., 150.8.60.20), the system automatically retrieves the **Parent Section** (150.8.60) and the **General Chapter Rules** (150.10) to ensure full context is available for "lesser of" logic.

---

## 5. Dedicated ETL Data Pipeline

### 5.1 Regulatory Knowledge ETL (Section-Aware)

| Stage         | Process                                                                                                                                                                                                                             |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Transform** | Regex-based section identification (headers ##, ###); metadata enrichment with parent-child links; isolating specific articles for hierarchical retrieval.                                                                           |

---

## 10. Service Provider Cost Estimation (Gemini 3)

The following estimates are based on a projected volume of **1,000 permit submissions per month**, using current (March 2026) pricing.

| Component                             | Model                             | Cost per Submission | Monthly (1,000) |
| ------------------------------------- | --------------------------------- | ------------------: | --------------: |
| Blueprint Reading (Vision)            | Claude 4.6 / Gemini 3.1 Pro       |              ~$0.20 |            $200 |
| Logic Auditor (Peer Review)           | Gemini 3.1 Pro                    |              ~$0.05 |             $50 |
| Validator Agents (×6 concurrent)      | Gemini 3 Flash                    |              ~$0.02 |             $20 |
| **AI Total (with Caching)**           |                                   |          **~$0.27** |       **~$270** |

---

## 12. Technical Integrity & QA Framework (New)

The system is validated using a dedicated **Evaluation Pipeline** (`eval_pipeline.py`).

### 12.1 Ground Truth Benchmarking
- **Evaluator Persona:** Senior Professional Engineer (P.Eng.) with 10+ years experience specializing in Toronto permit review.
- **Dataset:** 50 "Hard" Examiner's Notices with professional gold-standard responses.
- **Grading Rubric:** 
    - **Citation Accuracy:** Strict hierarchy check (Parent + Subsection).
    - **Completeness:** Quantitative proof requirement (Technical Matrix).
    - **Professional Tone:** BCIN-qualified authority.
- **Pass Threshold:** Zero tolerance for regulatory errors (Overall Pass only if all scores ≥ 9/10).
