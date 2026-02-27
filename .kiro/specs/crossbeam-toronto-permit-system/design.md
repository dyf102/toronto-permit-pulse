# System Design Document: CrossBeam Toronto Permit System

**Version:** 2.0 — Revised  
**Date:** February 27, 2026

---

## 1. Introduction & Overview

CrossBeam Toronto is an AI-powered permit correction response system targeting Garden Suites and Laneway Suites in the City of Toronto. The system ingests user-uploaded architectural plans and Examiner's Notices, orchestrates a suite of specialized AI agents to evaluate regulatory compliance (Zoning By-law 569-2013, OBC, Municipal Code Chapter 813, etc.), asks clarifying questions when necessary, and generates a complete resubmission package with citation-backed responses.

This design document translates the product requirements (v2.0) into a technical system architecture, with emphasis on front-end user experience, robust backend orchestration, AI interaction flows, and cost-efficient infrastructure to meet the < 5 minute processing SLA.

### 1.1 Revision Notes

This revision addresses the following issues from v1.0:

- **Model references updated:** All references to Claude have been corrected to Gemini 2.5 Pro (model ID `gemini-2.5-pro`) and Gemini 2.5 Flash.
- **Cost estimation recalculated:** The token consumption model has been revised to reflect Gemini's improved efficiency (fewer tokens per task) and correct pricing, along with a more granular breakdown of vision vs. text agent costs.
- **Backend stack clarified:** The original CrossBeam (California) uses Express.js on Cloud Run. This design uses Python (FastAPI) for the orchestrator. Section 4 now includes the rationale: Python's mature ecosystem for PDF processing (PyMuPDF, pdfplumber), ML/NLP pipelines, and the Google GenAI SDK makes it a stronger fit for the backend orchestration layer. The frontend remains Next.js.
- **Fire access validation corrected:** All references to fire access paths now use the verified suite-type-specific widths: 1.0 m for Garden Suites, 0.9 m for Laneway Suites — not the 6 m vehicle fire route width that appeared in the v1.0 requirements.
- **ETL pipeline section expanded:** Added detail on regulatory change detection cadence, vector embedding strategy, and blueprint segmentation for the Vision Service.
- **New section added:** Section 8 (Data Flow Sequence Diagram) provides a concrete walkthrough of a typical submission lifecycle.

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
│  │  │  (Opus 4.5    │  │  Parser      │  │                  │  │   │
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
│  │  ~29 reference files: By-law 569-2013, OBC Part 9,          │  │
│  │  Chapter 813, O. Reg. 462/24, City guidelines                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Component Summary

| Layer                      | Technology                                             | Responsibility                                                                                     |
| -------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Frontend                   | Next.js (React) + TypeScript, Vercel Edge              | Intake wizard, chunked upload, live agent dashboard, clarification loop, response review, download |
| API Gateway & Orchestrator | Python (FastAPI), Cloud Run / ECS Fargate              | State machine, agent coordination, WebSocket/SSE push, session management                          |
| AI Agent Sandboxes         | Containerized Google GenAI SDK instances               | 13 specialized agents running in isolation with access to their assigned knowledge files           |
| Vision Service             | Gemini 2.5 Pro (`gemini-2.5-pro`)                      | Reading architectural plans and Examiner's Notices page by page                                    |
| ETL Pipeline               | Celery / Prefect workers, event-driven via SQS/Pub-Sub | Regulatory knowledge updates (batch), blueprint segmentation (event-driven)                        |
| Knowledge Base             | pgvector (or managed Qdrant) + PostgreSQL              | ~29 reference files chunked, embedded, and versioned with effective dates                          |
| Object Storage             | S3 / GCS                                               | 250 MB PDF uploads, generated response packages, session artifacts                                 |
| Cache & Queue              | Redis + SQS/Pub-Sub                                    | Low-latency state handling, event-driven worker triggers                                           |

---

## 3. Front-End Design & User Experience

CrossBeam Toronto is deployed as a standalone web product at **`https://permit-pulse.ca/`**, sharing a design system with the broader CrossBeam tool suite for consistent branding.

### 3.1 Core User Flows

**Flow 1 — Intake & Discovery**

A step-by-step wizard collecting property address, suite type (Garden or Laneway), laneway abutment confirmation, and optional pre-approved plan reference. The system provides immediate feedback on eligibility: if the address maps to a former municipal zoning by-law (Etobicoke, North York, Scarborough, York, or East York), the wizard displays a clear notice that automated compliance validation is not available in the MVP and directs the user to contact Toronto Building at 416-397-5330.

**Flow 2 — Document Ingestion**

Resumable, chunked drag-and-drop uploads using pre-signed URLs for direct-to-storage transfer. Two dedicated dropzones: one for Architectural Plans, one for the Examiner's Notice. Client-side validation enforces the 250 MB limit, PDF format, and standardized sheet sizes. A progress bar reflects upload status with automatic retry on network interruption.

**Flow 3 — Analysis & Orchestration**

Given the 5-minute SLA, a static spinner is insufficient. The UI renders an **Agent Execution Pipeline** — a live telemetry panel showing active agents and their progress. Example transitions:

> ✓ Blueprint Reader — extracted 18 pages, 47 dimensions identified  
> ● Footprint Validator — verifying By-law 569-2013, Section 150.8.60…  
> ○ Fire Access Validator — queued  
> ○ Tree Protection Assessor — queued

Each agent transitions from queued → active → complete (or → clarification needed), giving the user confidence that work is progressing.

**Flow 4 — Clarification Loop**

If an agent identifies missing data (e.g., lot frontage not labeled on plans, tree proximity unknown), execution pauses. The UI surfaces a focused modal with the specific question, contextual explanation of why the information is needed, and input fields. Once answered, the pipeline resumes from the paused agent. Questions are batched where possible to minimize interruptions.

**Flow 5 — Review & Output**

A split-view dashboard:

- **Left panel:** The original Examiner's Notice with each deficiency item highlighted and numbered.
- **Right panel:** The generated response for each item, with regulatory citations, compliance status (resolved / drawing revision needed / variance required / LDA required), and confidence indicators.

A prominent Professional Liability Disclaimer requires acknowledgment before the Resubmission Package can be downloaded. The package includes the response document, cover letter, and a revision summary — all formatted as a single PDF per City resubmission guidelines.

### 3.2 Frontend Tech Stack

| Concern          | Choice                                                                              | Rationale                                                                                      |
| ---------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Framework        | Next.js (React) + TypeScript                                                        | Strong typing for the regulatory domain model; SSR for initial load performance                |
| Styling          | Tailwind CSS + shadcn/ui (Radix primitives)                                         | Accessible, professional aesthetic with minimal custom CSS; consistent with municipal-grade UX |
| State Management | Zustand (global workflow state) + TanStack Query (server state, polling, WebSocket) | Clean separation of client state and server-synced data                                        |
| PDF Viewing      | `react-pdf` with custom overlay layer                                               | Allows users to view uploaded plans with AI-identified annotations inline                      |
| Upload           | `tus` protocol or equivalent resumable uploader                                     | Handles 250 MB uploads reliably over variable network conditions                               |
| Real-time        | WebSocket (primary) with SSE fallback                                               | Agent status updates, clarification prompts, and pipeline completion events                    |

---

## 4. Backend Orchestration & AI Agents

### 4.1 Why Python (FastAPI) Instead of Express.js

The original CrossBeam (California) uses Express.js on Cloud Run. This Toronto implementation uses Python (FastAPI) for the orchestrator for three reasons:

1. **PDF processing ecosystem:** Python offers mature libraries for PDF text extraction (PyMuPDF, pdfplumber), OCR (Tesseract bindings), and image segmentation — all critical for the blueprint processing pipeline.
2. **Google GenAI SDK:** The Python SDK for Gemini provides native support for structured tool use, multi-turn agent conversations, and streaming — aligning with the agent sandbox architecture.
3. **ML/NLP tooling:** Vector embedding generation (sentence-transformers), semantic chunking, and knowledge retrieval (LangChain / LlamaIndex) are Python-first ecosystems.

The Express.js reference in the original CrossBeam architecture remains valid for the frontend's API routes and middleware (Next.js API routes), but the core orchestration logic benefits from Python's strengths.

### 4.2 Orchestration Workflow

The orchestrator operates as a state machine on the `PermitSession` entity:

```
INTAKE → UPLOADING → PARSING → ANALYZING → [CLARIFYING ↔ ANALYZING] → DRAFTING → COMPLETE
                                                                                    ↓
                                                                                  ERROR
```

**Step 1 — Ingestion & Parsing**

`Document_Ingestion_Service` receives an event when PDFs land in object storage. `PDF_Processor` extracts text; if visual blueprints are detected (low text density, high image content), pages are segmented into high-resolution image tiles and routed to the Vision Service (Gemini 2.5 Pro).

**Step 2 — Deficiency Extraction**

`Examiner_Notice_Parser` isolates and categorizes each deficiency item into: zoning, OBC, fire access, tree protection, servicing, soft landscaping, or other. The parser also distinguishes between an Examiner's Notice (deficiencies to address) and a Refusal Notice (formal refusal).

**Step 3 — Parallel Agent Execution**

To meet the < 5 minute SLA, agents execute in a parallel dependency graph:

```
Blueprint Reader ─────┐
                       ├──→ Suite Type Router ──┬──→ Footprint Validator
Examiner Notice Parser ┘                       ├──→ Height & Setback Validators
                                                ├──→ Fire Access Validator
Zoning Classifier ────────────────────────────→│    (1.0 m garden / 0.9 m laneway)
                                                ├──→ Tree Protection Assessor
                                                ├──→ Landscaping Validator
                                                └──→ Servicing Validator
                                                          │
                                        OBC Checker ◄─────┘
                                              │
                                   ┌──────────┴──────────┐
                                   ▼                      ▼
                           Citation Generator    Regulatory Updater
                                   │                      │
                                   └──────────┬───────────┘
                                              ▼
                                      Response Drafter
```

Agents in the same tier (Footprint, Fire Access, Tree, Landscaping) run concurrently once the Suite Type Router establishes the regulatory path. The OBC Checker waits for upstream validators to complete so it can incorporate their findings.

**Step 4 — Knowledge Retrieval (RAG)**

Each agent queries the Knowledge Base using the suite type and deficiency category as context. Retrieval is hybrid: vector similarity search (for semantic matching against chunked by-law text) combined with exact-match lookup (for specific section numbers cited in the Examiner's Notice). The Citation Generator binds all references against verified keys in the Knowledge Base — it cannot generate free-form citation strings.

**Step 5 — Synthesis & Response Drafting**

The Response Drafter compiles the final package:

- A written response addressing each deficiency in the order listed in the Examiner's Notice
- Regulatory citations for every claim
- A classification for each item: resolved, drawing revision needed, variance required, LDA required
- A professional cover letter referencing the permit application number
- A revision summary noting which drawing pages require resubmission

### 4.3 Clarification Handling

When an agent encounters a missing variable (e.g., `laneway_abutment_length: null`, `lot_frontage: null`), it yields a `CLARIFICATION_REQUIRED` state with a structured question payload. The orchestrator pauses the pipeline, pushes a WebSocket event to the frontend, and waits for the user's response. Once received, the pipeline resumes from the paused agent with the new data injected into its context.

Clarifications are batched: if multiple agents identify data gaps within the same execution tier, their questions are aggregated into a single user prompt to minimize round-trips.

---

## 5. Dedicated ETL Data Pipeline

A separate ETL pipeline operates asynchronously, handling both regulatory knowledge maintenance and heavy user file processing.

### 5.1 Regulatory Knowledge ETL (Batch)

| Stage         | Process                                                                                                                                                                                                                             | Tooling                                                                                      |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Extract**   | Scheduled scrape of City of Toronto Council updates, OLT rulings, amended by-law PDFs, and Ontario Gazette regulatory changes                                                                                                       | Celery Beat / Prefect scheduled flows; RSS monitoring for toronto.ca/city-government updates |
| **Transform** | Text extraction, OCR, semantic chunking by regulatory article (e.g., isolating Section 150.8.60 for Laneway Suite ancillary building requirements); metadata enrichment (effective date, superseded status, amending by-law number) | PyMuPDF, Tesseract, custom chunking pipeline                                                 |
| **Load**      | Generate dense vector embeddings of chunked rules; push to vector database with version tags; update structured relational records for exact-match citation lookup                                                                  | sentence-transformers, pgvector / Qdrant, PostgreSQL                                         |
| **Cadence**   | Weekly batch for stable regulatory corpus; ad-hoc trigger for major Council decisions or by-law amendments                                                                                                                          | Webhook triggers from monitoring, manual admin trigger                                       |

### 5.2 Blueprint & Document Processing ETL (Event-Driven)

When a user uploads a 250 MB architectural set to object storage, an event (SQS / Pub-Sub) triggers the processing worker:

| Stage         | Process                                                                                                                                                                                                                                                                                                                                                      |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Extract**   | Stream the raw PDF from cloud storage; identify page types (text-heavy Examiner's Notice vs. visual blueprint pages)                                                                                                                                                                                                                                         |
| **Transform** | For text pages: NLP extraction of deficiency items, regulatory citations, and examiner actions. For blueprint pages: flatten CAD/PDF layers, segment into high-resolution image tiles optimized for the Vision Service (Gemini 2.5 Pro). Tile size is calibrated to fit within the model's context window while preserving dimension labels and annotations. |
| **Load**      | Structured output (extracted dimensions, bounding boxes, text arrays, deficiency items) loaded into PostgreSQL and Redis cache. Pipeline transitions the `PermitSession` to the ANALYZING state.                                                                                                                                                             |

---

## 6. Core Data Models

### 6.1 PermitSession

| Field                        | Type                 | Description                                                                                  |
| ---------------------------- | -------------------- | -------------------------------------------------------------------------------------------- |
| `id`                         | UUID                 | Primary key                                                                                  |
| `status`                     | Enum                 | `INTAKE`, `UPLOADING`, `PARSING`, `ANALYZING`, `CLARIFYING`, `DRAFTING`, `COMPLETE`, `ERROR` |
| `property_address`           | String               | Toronto street address                                                                       |
| `suite_type`                 | Enum                 | `GARDEN`, `LANEWAY`                                                                          |
| `bylaw_context`              | String               | Applicable zoning by-law (e.g., "569-2013" or former municipal identifier)                   |
| `is_former_municipal_zoning` | Boolean              | True if property falls under a pre-amalgamation by-law                                       |
| `laneway_abutment_length`    | Float (nullable)     | Length of lot line abutting public laneway (metres); null for garden suites                  |
| `pre_approved_plan_number`   | String (nullable)    | City pre-approved plan reference if applicable                                               |
| `created_at`                 | Timestamp            | Session creation time                                                                        |
| `completed_at`               | Timestamp (nullable) | Processing completion time                                                                   |

### 6.2 DeficiencyItem

| Field              | Type    | Description                                                                            |
| ------------------ | ------- | -------------------------------------------------------------------------------------- |
| `id`               | UUID    | Primary key                                                                            |
| `session_id`       | UUID    | FK → PermitSession                                                                     |
| `category`         | Enum    | `ZONING`, `OBC`, `FIRE_ACCESS`, `TREE_PROTECTION`, `LANDSCAPING`, `SERVICING`, `OTHER` |
| `raw_notice_text`  | Text    | Original text from Examiner's Notice                                                   |
| `extracted_action` | Text    | Parsed action required by examiner                                                     |
| `agent_confidence` | Float   | 0.0–1.0 confidence score from the parsing agent                                        |
| `order_index`      | Integer | Position in the original notice (for response ordering)                                |

### 6.3 GeneratedResponse

| Field                | Type              | Description                                                                                |
| -------------------- | ----------------- | ------------------------------------------------------------------------------------------ |
| `id`                 | UUID              | Primary key                                                                                |
| `deficiency_id`      | UUID              | FK → DeficiencyItem                                                                        |
| `draft_text`         | Text              | Response text addressing the deficiency                                                    |
| `citations`          | JSONB             | Array of `{ bylaw, section, version, effective_date }`                                     |
| `resolution_status`  | Enum              | `RESOLVED`, `DRAWING_REVISION_NEEDED`, `VARIANCE_REQUIRED`, `LDA_REQUIRED`, `OUT_OF_SCOPE` |
| `variance_magnitude` | String (nullable) | e.g., "side setback: 0.3 m provided, 0.6 m required"                                       |
| `agent_reasoning`    | Text              | Logged reasoning chain for audit trail                                                     |

### 6.4 ClarificationExchange

| Field           | Type                 | Description                            |
| --------------- | -------------------- | -------------------------------------- |
| `id`            | UUID                 | Primary key                            |
| `session_id`    | UUID                 | FK → PermitSession                     |
| `agent_name`    | String               | Agent that triggered the clarification |
| `question_text` | Text                 | Question presented to the user         |
| `user_response` | Text (nullable)      | User's answer                          |
| `asked_at`      | Timestamp            | When the question was surfaced         |
| `answered_at`   | Timestamp (nullable) | When the user responded                |

---

## 7. Infrastructure as Code (IaC) & Deployment

The entire system infrastructure is defined, provisioned, and managed using **Terraform**, ensuring reproducibility, scalability, and version-controlled infrastructure changes.

### 7.1 Infrastructure Components

| Component          | Terraform-Managed Resources                                                                                                  |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| Core Orchestration | Managed Kubernetes (EKS / GKE) or serverless containers (ECS Fargate / Cloud Run) for FastAPI backend and AI Agent Sandboxes |
| Data & Queue Layer | PostgreSQL (RDS / Cloud SQL) with pgvector extension, Redis (ElastiCache / Memorystore), event queues (SQS / Pub-Sub)        |
| Storage            | S3 / GCS buckets with strict IAM roles, bucket policies, CORS configuration, and lifecycle rules (90-day retention)          |
| ETL Environment    | Celery / Prefect worker instances, scheduled task definitions                                                                |
| Vector Database    | pgvector on the PostgreSQL instance (budget option) or managed Qdrant (production option)                                    |
| Frontend           | Vercel project configuration (DNS, edge functions, environment variables)                                                    |

### 7.2 CI/CD Integration

- Terraform execution is integrated into the CI/CD pipeline (GitHub Actions). Infrastructure changes require a Pull Request with an automated `terraform plan` output for review.
- Environment parity (Development, Staging, Production) is maintained through parameterized Terraform workspaces.
- Application deployments use container image promotion: build once, test in staging, promote the identical image to production.

### 7.3 Security & Compliance

| Concern         | Approach                                                                                                                                                  |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Data at rest    | AES-256 encryption on all storage (S3/GCS default, RDS/Cloud SQL encryption enabled)                                                                      |
| Data in transit | TLS 1.3 for all connections; HTTPS-only frontend                                                                                                          |
| PII handling    | Property addresses and uploaded plans are automatically purged after 90 days per the audit trail retention policy; no PII is stored in the Knowledge Base |
| Access control  | IAM roles scoped per service; no shared credentials; API keys rotated on schedule                                                                         |
| Audit trail     | All agent decisions, user clarifications, and generated citations tied to the `PermitSession` for debugging and accuracy review                           |
| Upload security | Pre-signed URLs with 15-minute expiry; server-side virus scanning on upload completion                                                                    |

---

## 8. Data Flow Sequence — Typical Submission

The following walkthrough illustrates a typical 10-item Examiner's Notice for a laneway suite:

```
User                    Frontend           Object Storage    Orchestrator         Agents
 │                         │                     │               │                  │
 │─── Fill intake form ───→│                     │               │                  │
 │                         │── POST /session ────────────────────→│                  │
 │                         │◄── session_id ──────────────────────│                  │
 │                         │                     │               │                  │
 │─── Upload plans ───────→│                     │               │                  │
 │                         │── Get pre-signed URL ──────────────→│                  │
 │                         │── PUT 250MB PDF ───→│               │                  │
 │                         │                     │── Event ──────→│                  │
 │                         │                     │               │── Parse PDF ─────→│
 │                         │                     │               │                  │
 │─── Upload notice ──────→│                     │               │                  │
 │                         │── PUT notice PDF ──→│               │                  │
 │                         │                     │── Event ──────→│                  │
 │                         │                     │               │── Parse notice ──→│
 │                         │                     │               │                  │
 │                         │◄── WS: "ANALYZING" ────────────────│                  │
 │                         │                     │               │                  │
 │                         │◄── WS: "Blueprint Reader active" ──│◄── dimensions ───│
 │                         │◄── WS: "Fire Access Validator" ────│◄── 0.9m check ──│
 │                         │◄── WS: "Tree Assessor" ────────────│◄── TPZ flags ────│
 │                         │                     │               │                  │
 │                         │◄── WS: "CLARIFYING" ───────────────│                  │
 │◄── "What is your lot frontage?" ─────────────│               │                  │
 │─── "7.2 m" ───────────→│── POST /clarify ────────────────────→│                  │
 │                         │                     │               │── Resume agents ─→│
 │                         │                     │               │                  │
 │                         │◄── WS: "Citation Generator" ───────│◄── citations ────│
 │                         │◄── WS: "Response Drafter" ─────────│◄── package ──────│
 │                         │◄── WS: "COMPLETE" ─────────────────│                  │
 │                         │                     │               │                  │
 │◄── Review split view ──│                     │               │                  │
 │─── Acknowledge disclaimer ──→│               │               │                  │
 │─── Download package ───→│── GET /package ─────────────────────→│                  │
 │◄── Resubmission PDF ───│                     │               │                  │
```

---

## 9. Edge Cases & Technical Risk Mitigation

| Edge Case                         | Risk                                                                            | Mitigation Strategy                                                                                                                                                                                            |
| --------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Large file uploads (250 MB)**   | API memory bloat, timeouts                                                      | Pre-signed URLs for direct-to-storage upload; frontend uploads bypass the API entirely; backend receives completion webhook                                                                                    |
| **Legacy zoning detection**       | Incorrect regulation applied to properties under former municipal by-laws       | Early interception in intake wizard; address lookup against known pre-amalgamation boundaries; explicit flag that automated validation is excluded in MVP                                                      |
| **Fire access spatial nuance**    | Incorrect width validated (1.0 m vs. 0.9 m)                                     | Suite type strictly gates which Fire_Access_Validator ruleset is applied; Vision Service measures actual path width from plans; LDA detection module triggers when width is unachievable within property lines |
| **Citation hallucination**        | AI generates non-existent by-law references                                     | Citation Generator operates under strict schema validation; every citation must bind against a verified key in the Knowledge Base; free-form citation strings are rejected                                     |
| **Vision extraction errors**      | AI misreads dimensions or annotations                                           | Confidence scoring on all extracted measurements; low-confidence values trigger clarification questions; user can manually override extracted dimensions                                                       |
| **Stale regulatory data**         | By-law amended since last Knowledge Base update                                 | Regulatory Updater agent performs live web search before drafting; weekly batch ETL catches stable changes; all knowledge files carry effective dates and superseded flags                                     |
| **O. Reg. 462/24 misapplication** | Regulation applied to property with > 3 residential units (not qualifying)      | Zoning Classifier verifies unit count before applying O. Reg. provisions; explicit check in Suite Type Router                                                                                                  |
| **Angular plane ambiguity**       | O. Reg. 462/24 eliminated the requirement, but City may still apply constraints | System flags as a nuance requiring confirmation with the examiner rather than asserting full elimination                                                                                                       |
| **PDF with CAD layers**           | Multi-layer blueprints render incorrectly or lose dimension data                | ETL flattens CAD layers before segmentation; fallback to full-page Vision processing if layer extraction fails                                                                                                 |

---

## 10. Service Provider Cost Estimation

The following estimates are based on a projected volume of **1,000 permit submissions per month**, using current (February 2026) pricing.

### 10.1 AI Service — Google Gemini 2.5 Series

The heaviest variable cost is Vision processing of architectural plans using Gemini 2.5 Pro.

| Component                             | Model                             | Token Estimate per Submission                                       | Cost per Submission | Monthly (1,000) |
| ------------------------------------- | --------------------------------- | ------------------------------------------------------------------- | ------------------: | --------------: |
| Blueprint Reading (Vision)            | Gemini 2.5 Pro (`gemini-2.5-pro`) | ~20 pages × ~2,000 input tokens/page = 40,000 input + ~5,000 output |              ~$0.15 |            $150 |
| Examiner Notice Parsing               | Gemini 2.5 Flash                  | ~8,000 input + ~3,000 output                                        |              ~$0.01 |             $10 |
| Validator Agents (×6 concurrent)      | Gemini 2.5 Flash                  | ~10,000 input + ~4,000 output per agent × 6                         |              ~$0.05 |             $50 |
| Citation Generator + Response Drafter | Gemini 2.5 Flash                  | ~15,000 input + ~8,000 output                                       |              ~$0.02 |             $20 |
| Regulatory Updater (Web Search)       | Gemini 2.5 Flash                  | ~5,000 input + ~2,000 output                                        |              ~$0.01 |             $10 |
| **AI Total**                          |                                   |                                                                     |          **~$0.24** |       **~$240** |

**Optimization levers:**

- **Context Caching:** Regulatory knowledge context (system prompts with by-law text) can be heavily cached.
- **Batch API:** For non-urgent reprocessing.
- **Model tiering:** Tree Protection Assessor and Landscaping Validator handle simpler rule checks and could run on Gemini 1.5 Flash-8B instead of Gemini 2.5 Flash, saving even more.

### 10.2 Cloud Infrastructure

| Component                        | Service                                                       | Monthly Cost |
| -------------------------------- | ------------------------------------------------------------- | -----------: |
| Compute (orchestrator + workers) | ECS Fargate / Cloud Run (serverless)                          |        ~$150 |
| Object Storage                   | S3 / GCS (250 GB/month new, 750 GB max with 90-day retention) |         ~$15 |
| Relational DB + pgvector         | RDS PostgreSQL / Cloud SQL (db.t3.medium equivalent)          |         ~$70 |
| Cache + Message Queue            | ElastiCache Redis (t3.micro) + SQS/Pub-Sub                    |         ~$40 |
| **Infrastructure Total**         |                                                               |    **~$275** |

### 10.3 Vector Database & Search

| Option                                   |        Monthly Cost |
| ---------------------------------------- | ------------------: |
| pgvector on existing PostgreSQL (budget) | $0 (included above) |
| Managed Qdrant Cloud (production)        |                ~$70 |

### 10.4 Frontend Hosting

| Component       | Service                                       | Monthly Cost |
| --------------- | --------------------------------------------- | -----------: |
| permit-pulse.ca | Vercel Pro (edge hosting, CDN, custom domain) |         ~$20 |

### 10.5 Total — Production (1,000 submissions/month)

| Category                   | Monthly Cost |
| -------------------------- | -----------: |
| AI Services (Gemini 2.5)   |        ~$240 |
| Cloud Infrastructure       |        ~$275 |
| Vector Database (pgvector) |           $0 |
| Frontend Hosting           |          $20 |
| **Total**                  |    **~$535** |

*Note: With context caching and model tiering optimizations fully applied, the AI cost could drop significantly, bringing the total cost per submission even lower.*

### 10.6 Budget Starter Option (MVP Validation, < 100 submissions/month)

For early market validation at low volume:

| Category       | Approach                                                             | Monthly Cost |
| -------------- | -------------------------------------------------------------------- | -----------: |
| AI Services    | Gemini 2.5 Pro for Vision only; Gemini 2.5 Flash for all text agents |         ~$15 |
| Compute        | Cloud Run / Lambda scale-to-zero (free tier)                         |          ~$0 |
| Database       | Supabase / Neon free tier with pgvector                              |          ~$0 |
| Object Storage | S3/GCS free tier (< 25 GB)                                           |          ~$0 |
| Frontend       | Vercel Hobby tier                                                    |          ~$0 |
| **Total**      |                                                                      |     **~$30** |

*Scales to the production tier by switching Terraform workspaces when volume justifies the infrastructure investment.*

---

## 11. Monitoring & Observability

| Concern                  | Tool                               | Metrics                                                                 |
| ------------------------ | ---------------------------------- | ----------------------------------------------------------------------- |
| API latency & errors     | Datadog / CloudWatch               | P50/P95/P99 response times, error rates by endpoint                     |
| Agent execution          | Custom telemetry → dashboard       | Per-agent execution time, confidence scores, clarification trigger rate |
| SLA compliance           | Alerting on PermitSession duration | % of sessions completing within 5 minutes; alert if > 10% breach SLA    |
| Knowledge Base freshness | ETL pipeline monitoring            | Days since last successful regulatory update; alert if > 14 days stale  |
| Cost tracking            | Cloud billing dashboards           | Daily AI token spend, per-submission cost trending, anomaly detection   |
| Upload success rate      | Object storage event logs          | Failed uploads, retry counts, average upload duration for 250 MB files  |