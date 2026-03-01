# Project TODO & Technical Debt

This document tracks known limitations, technical debt, and planned improvements for the CrossBeam Toronto Permit System.

## 🔴 High Priority (Technical Integrity & Accuracy)

- [ ] **Dual-Constraint Engine Hardening:** Ensure all agents (not just Zoning) explicitly check for "lesser of/greater of" logic in the Knowledge Base. (Effort: **Small**, Created: 2026-03-01)
- [ ] **Quantitative Matrix Enforcement:** Refactor frontend to display the technical matrix (Required vs. Proposed) in a structured UI component, not just raw text. (Effort: **Small**, Created: 2026-03-01)
- [ ] **Log Advanced Auditor Feedback:** Persist all feedback and revised drafts from the `Logic_Auditor` (Reviewer Agent) into the database for analysis and recursive prompt improvement. (Effort: **Small**, Created: 2026-03-01)
- [ ] **LLM Backend Caching Research:** Research and implement semantic or exact-match caching for LLM calls (e.g., Redis, GPTCache, or LangChain Cache) to reduce costs and latency. Evaluate cost/efficiency of semantic vs. literal caching. (Effort: **Medium**, Created: 2026-03-01)
- [ ] **Hallucination Guardrail:** Implement a strict "Citation Binding" layer that cross-references AI-generated section numbers against the DB metadata before rendering. (Effort: **Medium**, Created: 2026-03-01)
- [ ] **Ground Truth Dataset:** Curate the full set of 50 "hard" Examiner's Notices for automated regression testing in `eval_pipeline.py`. (Effort: **Medium**, Created: 2026-03-01)

## 🟡 Medium Priority (Geographic & Regulatory Scope)

- [x] **Legacy Case Boundary Detection:** Refine frontend wizard to detect Annex/Yorkville exclusion zones and high-risk legacy boundaries (Waterfront, Railway Lands). (Effort: **Small**, Created: 2026-03-01, Completed: 2026-03-01, PR: 0cb25a3)
- [ ] **Legacy Zoning API Integration:** Replace keyword-based detection in `IntakeWizard.tsx` with a Latitude/Longitude lookup against the Toronto Open Data Zoning By-law Index. (Effort: **Medium**, Created: 2026-03-01)
- [ ] **Annex/Yorkville Logic:** Implement specific validation logic for By-law 438-86 to support the Annex/Yorkville exclusion zones instead of just blocking them. (Effort: **Large**, Created: 2026-03-01)
- [ ] **Former Municipality Ingestion:** Ingest the core zoning codes for Etobicoke (No. 7625), North York, and Scarborough into the RAG Knowledge Base. (Effort: **Large**, Created: 2026-03-01)
- [ ] **OBC Part 11 Support:** Add specialized knowledge files for Renovation (Part 11) to support Secondary Suite conversions. (Effort: **Medium**, Created: 2026-03-01)

## 🔵 Low Priority (User Experience & Automation)

- [ ] **Automated Drawing Markup:** Implement the `reportlab` logic to generate PDF "Revision Bubbles" on architectural plans based on AI-identified deficiencies. (Effort: **Large**, Created: 2026-03-01)
- [ ] **Large File Handling (250MB):** Implement Pre-signed URL uploads to Object Storage (S3/GCS) to prevent backend memory exhaustion. (Effort: **Medium**, Created: 2026-03-01)
- [ ] **Bilingual Support:** Prepare Knowledge Base for French translations of OBC provisions. (Effort: **Small**, Created: 2026-03-01)
- [ ] **GTA Expansion:** Modularize the validator logic to support Mississauga and Vaughan by-laws. (Effort: **Large**, Created: 2026-03-01)

## 🛠️ Technical Debt

- [x] **Python 3.11 Environment Standardization:** Upgrade the local virtual environment from 3.9 to 3.11 to match the production Docker container. (Effort: **Small**, Created: 2026-03-01, Completed: 2026-03-01, PR: 0cb25a3)
- [x] **Modernize Backend Syntax:** Refactor backend files to use `| None` instead of `Optional[]` and `list[]` instead of `List[]`. (Effort: **Small**, Created: 2026-03-01, Completed: 2026-03-01, PR: 0cb25a3)
- [ ] **Recursive RAG Latency:** The current recursive retrieval adds ~2-3 seconds to the processing loop. Optimize SQLAlchemy queries to use JSONB indexing for parent-child lookups. (Effort: **Medium**, Created: 2026-03-01)
- [ ] **Mock Data Cleanup:** Revert `eval_pipeline.py` mock responses once real-world benchmark data is fully integrated. (Effort: **Small**, Created: 2026-03-01)
- [ ] **Rate Limit Resilience:** Transition from simple `time.sleep()` to a robust task queue (Celery/Redis) for managing Gemini/Claude API quotas. (Effort: **Medium**, Created: 2026-03-01)
