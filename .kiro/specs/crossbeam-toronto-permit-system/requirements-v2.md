# Requirements Document: CrossBeam Toronto Permit System

**Version:** 2.0 — Revised  
**Date:** February 27, 2026

---

## Introduction

CrossBeam Toronto is an AI-powered permit correction response system designed to streamline Toronto's building permit process for Laneway Suites and Garden Suites. The system addresses correction-cycle bottlenecks by analyzing architectural plans and Examiner's Notices, then generating complete correction-response packages ready for resubmission to the City of Toronto.

The system leverages Toronto-specific regulatory knowledge including the Ontario Building Code, Toronto Zoning By-law 569-2013, Ontario Regulation 462/24, and multiple city-specific by-laws to provide accurate, citation-backed responses that meet professional standards.

---

## Revision Notes

This revision corrects several substantive errors in the original v1.0 requirements and adds missing regulatory detail. Key changes:

- **Requirement 6 (Fire Access):** Corrected path width from 6 metres (a fire route/road standard) to the actual pedestrian access path requirements: 1.0 m for garden suites, 0.9 m for laneway suites. Added suite-type-specific fire access rules, Limiting Distance Agreement provisions, fire hydrant proximity rules, and the 90 m extended travel distance option.
- **Requirement 5 (Zoning):** Added laneway suite maximum footprint dimensions (10.0 m × 8.0 m), laneway frontage requirement (3.5 m minimum), lot coverage limits (30% for laneway suites; combined 20% for all backyard buildings with garden suites), soft landscaping percentages, and bicycle parking mandate.
- **Requirement 4 (Blueprint Reader):** Added extraction of soft landscaping areas, bicycle parking, servicing routes, and Limiting Distance Agreement paths.
- **Requirement 8 (OBC):** Added plumbing separation rule (OBC 7.1.2.4(2)), sprinkler requirements, qualified designer stamp obligations, and energy efficiency provisions.
- **New Requirement 26:** Servicing and utilities compliance.
- **New Requirement 27:** Soft landscaping and site coverage validation.
- **New Requirement 28:** Limiting Distance Agreement detection.
- Expanded glossary, regulatory references, and edge case coverage throughout.

---

## Glossary

| Term | Definition |
|------|-----------|
| **System** | The CrossBeam Toronto permit correction response system |
| **Examiner_Notice** | Official document from City of Toronto identifying deficiencies in a permit application (also called "Notice of Examiner's Comments" or "Refusal Notice") |
| **Architectural_Plans** | PDF documents containing building drawings, site plans, and technical specifications |
| **Response_Package** | Complete set of documents addressing all deficiencies identified in the Examiner's Notice |
| **Suite_Type** | Classification of the structure as either Garden Suite or Laneway Suite |
| **Zoning_Validator** | Component that verifies compliance with Toronto Zoning By-law 569-2013 |
| **OBC_Checker** | Component that verifies compliance with Ontario Building Code |
| **Blueprint_Reader** | AI component that extracts information from architectural drawings |
| **Document_Ingestion_Service** | Component that processes and extracts data from uploaded PDF documents |
| **Orchestrator** | Express.js service that coordinates AI agents and workflow execution |
| **Knowledge_Base** | Repository of regulatory documents, by-laws, and reference materials |
| **Pre_Approved_Plan** | City-approved standardized design that can be referenced for compliance |
| **Setback** | Minimum required distance between a structure and property lines |
| **Angular_Plane** | Three-dimensional zoning envelope that limits building height and massing (eliminated by O. Reg. 462/24 for qualifying ARUs, though the City notes existing limitations may still apply in practice) |
| **Tree_Protection_Zone (TPZ)** | Area around protected trees where construction is restricted per Municipal Code Chapter 813 |
| **Fire_Access_Path** | Required clear pedestrian pathway for firefighter access — not a vehicle fire route |
| **Heritage_Overlay** | Additional zoning restrictions for properties in heritage conservation districts |
| **Variance** | Official permission from the Committee of Adjustment to deviate from zoning requirements |
| **Former_Municipal_Zoning** | Legacy zoning rules from pre-amalgamation municipalities (Etobicoke, North York, Scarborough, York, East York) that are not covered by By-law 101-2022 for garden suites |
| **Limiting_Distance_Agreement (LDA)** | Legal agreement registered on title allowing shared use of a neighbouring property's side yard for fire access |
| **ZALC** | Zoning Applicable Law Certificate — documents how a proposal fits zoning and applicable laws; required for a complete permit application |
| **BCIN_Designer** | Building Code Identification Number holder — a qualified designer authorized under the Ontario Building Code |
| **Footprint_Validator** | Component that verifies building size compliance |
| **Height_Validator** | Component that verifies building height compliance |
| **Setback_Validator** | Component that verifies setback distance compliance |
| **Fire_Access_Validator** | Component that verifies emergency access compliance |
| **Tree_Protection_Assessor** | Component that evaluates tree protection requirements |
| **Landscaping_Validator** | Component that verifies soft landscaping percentage and site coverage |
| **Servicing_Validator** | Component that evaluates utility connection compliance |
| **Citation_Generator** | Component that produces accurate regulatory references |
| **PDF_Processor** | Component that handles PDF file parsing and extraction |
| **Vision_Service** | Claude Opus service for reading and interpreting visual plan elements |
| **Agent_Sandbox** | Isolated execution environment for AI agents |
| **Resubmission_Package** | Final output containing corrected plans and response documentation |

---

## Requirements

### Requirement 1: Document Upload and Ingestion

**User Story:** As a permit applicant, I want to upload my architectural plans and Examiner's Notice, so that the system can analyze my permit deficiencies.

#### Acceptance Criteria

1. WHEN a user uploads a PDF file, THE Document_Ingestion_Service SHALL accept files up to 250 MB in size, consistent with the City of Toronto File Submission Hub limit.
2. WHEN architectural plans are uploaded, THE Document_Ingestion_Service SHALL extract text and visual elements from the PDF.
3. WHEN an Examiner's Notice is uploaded, THE Document_Ingestion_Service SHALL parse the document structure and extract deficiency items.
4. THE System SHALL require both architectural plans and Examiner's Notice before processing begins.
5. WHEN a PDF file exceeds 250 MB, THE System SHALL return an error message indicating the size limit.
6. THE PDF_Processor SHALL preserve the original document structure for reference during analysis.
7. THE System SHALL accept scanned Examiner's Notices and process them via OCR where text extraction yields insufficient content.
8. THE System SHALL validate that all uploaded drawings conform to the City's electronic submission guidelines (standardized sheet sizes, drawn to scale, fully dimensioned, signed and dated).

---

### Requirement 2: Property Information Collection

**User Story:** As a permit applicant, I want to provide my property details, so that the system can apply location-specific regulations.

#### Acceptance Criteria

1. THE System SHALL collect the property address from the user.
2. THE System SHALL collect the suite type designation (Garden Suite or Laneway Suite) from the user.
3. WHERE a pre-approved plan number is available, THE System SHALL accept the optional pre-approved plan reference.
4. WHEN a property address is provided, THE Zoning_Validator SHALL determine the applicable zoning designation.
5. THE System SHALL validate that the property address is within Toronto city limits.
6. WHEN a property address is provided, THE System SHALL determine whether the property is zoned under By-law 569-2013 or under a former municipal zoning by-law.
7. THE System SHALL collect whether the applicant has a current legal survey of the property.
8. THE System SHALL collect whether the lot abuts a public laneway and, if so, the length of the abutting lot line.

---

### Requirement 3: Examiner's Notice Parsing

**User Story:** As a permit applicant, I want the system to understand the deficiencies identified by the examiner, so that all issues are addressed in the response.

#### Acceptance Criteria

1. WHEN an Examiner's Notice is provided, THE System SHALL extract all deficiency line items.
2. THE System SHALL categorize each deficiency by type: zoning compliance, building code, fire access, tree protection, servicing, soft landscaping, or other.
3. THE System SHALL extract any specific regulatory citations mentioned in the Examiner's Notice.
4. THE System SHALL identify the examiner's requested actions for each deficiency.
5. WHEN a deficiency item is ambiguous, THE System SHALL flag it for clarification from the user.
6. THE System SHALL distinguish between an Examiner's Notice (deficiencies to address) and a Refusal Notice (formal refusal requiring all items to be resolved before resubmission).

---

### Requirement 4: Architectural Plan Analysis

**User Story:** As a permit applicant, I want the system to read my architectural drawings, so that it can verify measurements and design elements.

#### Acceptance Criteria

1. WHEN architectural plans are provided, THE Blueprint_Reader SHALL extract building dimensions including length and width.
2. THE Blueprint_Reader SHALL identify the building footprint area.
3. THE Blueprint_Reader SHALL extract building height measurements.
4. THE Blueprint_Reader SHALL identify setback distances from all property lines, including rear, side, and lane-facing boundaries.
5. THE Blueprint_Reader SHALL locate and measure fire access paths, including width, height clearance, and travel distance from the public street.
6. THE Vision_Service SHALL process visual elements that cannot be extracted as text.
7. THE Blueprint_Reader SHALL identify the location of trees and vegetation on site plans.
8. THE Blueprint_Reader SHALL extract the separation distance between the proposed suite and the main house.
9. THE Blueprint_Reader SHALL identify soft landscaping areas and calculate their percentage of the relevant yard area.
10. THE Blueprint_Reader SHALL identify servicing routes (water, sanitary, storm, hydro, gas) shown on the plans.
11. THE Blueprint_Reader SHALL identify bicycle parking provisions.
12. THE Blueprint_Reader SHALL detect whether a Limiting Distance Agreement path is shown on the site plan.

---

### Requirement 5: Toronto Zoning Compliance Validation

**User Story:** As a permit applicant, I want the system to verify zoning compliance, so that my resubmission meets Toronto Zoning By-law 569-2013 requirements.

#### Acceptance Criteria

1. WHEN a property address is provided, THE Zoning_Validator SHALL determine the applicable zoning designation under By-law 569-2013 and confirm the property is in a qualifying residential zone (R, RD, RS, RT, or RM).
2. FOR Garden Suites, THE Footprint_Validator SHALL verify that the building footprint does not exceed the lesser of 60 m² or 40% of the rear yard.
3. FOR Laneway Suites, THE Footprint_Validator SHALL verify that the building does not exceed 10.0 m in length and 8.0 m in width.
4. FOR Garden Suites, THE Footprint_Validator SHALL verify that the combined coverage of all backyard buildings (suite, garage, sheds) does not exceed 20% of the total lot area.
5. FOR Laneway Suites, THE Footprint_Validator SHALL verify that the laneway suite does not exceed 30% of the lot coverage.
6. THE Height_Validator SHALL verify building height against the separation-distance rules: maximum 4.0 m if the suite is less than 7.5 m from the main house; maximum 6.3 m if the suite is 7.5 m or more from the main house.
7. THE Setback_Validator SHALL verify all setbacks using suite-type-specific rules:
   - Garden Suite: rear setback typically 1.5 m; side setback the greater of 0.6 m or 10% of lot frontage, increased if openings are present.
   - Laneway Suite: 0.0 m side/rear setback permitted where no openings exist and the wall does not abut a street or lane; 1.5 m where abutting a lane or street; additional 1.5 m setback for portions above 4.0 m abutting another residential property's rear yard.
8. THE System SHALL verify the minimum separation distance between the suite and the main house: 4.0 m under O. Reg. 462/24 for suites up to 4.0 m in height; 7.5 m for suites exceeding 4.0 m in height.
9. WHEN angular plane requirements may apply, THE System SHALL flag that O. Reg. 462/24 eliminated the angular plane requirement for qualifying ARUs but note that the City's interpretation may still impose constraints in certain cases.
10. WHEN a zoning violation is detected, THE System SHALL identify the specific by-law section that is violated.
11. THE Zoning_Validator SHALL apply Ontario Regulation 462/24 provisions, including confirming the property qualifies (maximum three residential units on the lot).
12. FOR Laneway Suites, THE Zoning_Validator SHALL verify that the lot line abuts a public laneway by at least 3.5 m.
13. THE Zoning_Validator SHALL verify that the suite's floor area does not exceed the gross floor area of the main residence.
14. THE Zoning_Validator SHALL verify bicycle parking requirements (minimum 2 spaces for laneway suites).

---

### Requirement 6: Fire Access Path Validation

**User Story:** As a permit applicant, I want the system to verify fire access compliance, so that emergency personnel can safely reach the suite.

#### Acceptance Criteria

1. FOR Garden Suites, THE Fire_Access_Validator SHALL verify that a continuous, unobstructed pedestrian access path exists from the fronting public street to the suite entrance with a minimum width of **1.0 m** and a minimum vertical clearance of **2.1 m**.
2. FOR Laneway Suites, THE Fire_Access_Validator SHALL verify that a continuous, unobstructed pedestrian access path exists from the public street (via the side yard or via the laneway) to the suite entrance with a minimum width of **0.9 m** and a minimum vertical clearance of **2.1 m**.
3. THE Fire_Access_Validator SHALL verify that the travel distance from the public street to the suite entrance does not exceed **45 m**.
4. WHEN the travel distance exceeds 45 m but does not exceed **90 m**, THE System SHALL verify that at least one additional fire-safety measure acceptable to the City is incorporated. Acceptable measures include:
   - **Option 1:** Automatic sprinkler system, exterior strobe light, and interconnected smoke alarm/warning system designed by a professional engineer.
   - **Option 2:** Increased fire protection materials and non-combustible cladding on exterior walls, exterior strobe light, and interconnected smoke alarm/warning system designed by a professional engineer.
5. THE Fire_Access_Validator SHALL verify that a fire hydrant is located within **45 m** of where a firefighting vehicle would park (in front of the property or at the intersection of a flanking street and the laneway).
6. WHEN the fire access path width cannot be achieved entirely on the applicant's property, THE System SHALL flag that a **Limiting Distance Agreement** with the neighbouring property owner may be required and reference the City's template agreement process.
7. THE Fire_Access_Validator SHALL flag any obstructions in the access path (gates, fences, structures) that reduce the clear width below the minimum, noting that only localized protrusions such as hydro and gas meters are permitted.
8. FOR Garden Suites, THE System SHALL verify that the access path originates from the street the existing house faces (not from a rear laneway).
9. FOR Laneway Suites, THE System SHALL verify that the principal entrance is located on the laneway side.
10. WHEN a fire access deficiency is identified, THE System SHALL cite the specific Ontario Building Code sections (Div. B, 9.9.2.4 for principal access; Div. B, 9.10.20.3 for fire access) and the applicable City of Toronto fire access guidance document.

---

### Requirement 7: Tree Protection Assessment

**User Story:** As a permit applicant, I want the system to identify tree protection requirements, so that I comply with Toronto Municipal Code Chapter 813.

#### Acceptance Criteria

1. WHEN trees are identified on the site plan, THE Tree_Protection_Assessor SHALL determine if they are protected under Chapter 813, including trees on neighbouring properties whose root zones may be affected.
2. THE Tree_Protection_Assessor SHALL flag that an arborist report is almost always required for garden and laneway suite applications in Toronto.
3. WHEN construction may encroach on a tree protection zone, THE System SHALL identify the conflict and recommend the footprint be shaped around the TPZ.
4. THE Tree_Protection_Assessor SHALL reference the specific Chapter 813 provisions that apply.
5. WHEN a tree removal permit may be required, THE System SHALL flag this requirement and warn that fines for illegal removal range from $500 to $100,000 per tree.
6. THE System SHALL note that tree permit applications may be refused if harm to healthy, protected trees is likely, and that this can force project redesigns.
7. THE System SHALL flag trees with a trunk diameter of 30 cm or more as likely protected and requiring assessment.

---

### Requirement 8: Ontario Building Code Compliance

**User Story:** As a permit applicant, I want the system to verify building code compliance, so that my design meets OBC requirements.

#### Acceptance Criteria

1. THE OBC_Checker SHALL verify that the suite classification is appropriate for the intended use under OBC Part 9 (Housing and Small Buildings).
2. THE OBC_Checker SHALL verify that principal access requirements are met per OBC Div. B, 9.9.2.4.
3. THE OBC_Checker SHALL verify that fire separation requirements are met between the suite and principal dwelling per OBC Div. B, 9.10.
4. THE OBC_Checker SHALL verify the plumbing separation rule: under OBC 7.1.2.4(2), plumbing serving a dwelling unit shall not be installed in or under another unit unless the piping is located in a tunnel, pipe corridor, common basement, or parking garage and is accessible for servicing throughout its length.
5. WHEN an OBC violation is detected, THE System SHALL cite the specific OBC division, part, section, and article number.
6. THE OBC_Checker SHALL verify that accessibility requirements are addressed where applicable.
7. THE OBC_Checker SHALL verify that drawings bearing a professional engineer's seal include the Assumption of Responsibility for Engineering Content Form as required by Toronto Building.
8. THE OBC_Checker SHALL flag whether the drawings were prepared by a BCIN-qualified designer and whether the designer's name, registration number, qualification ID, signature, and stamp are present.
9. FOR suites using the 90 m extended fire access travel distance, THE OBC_Checker SHALL verify that the specified fire-safety measures (sprinkler system or enhanced fire protection materials) are reflected in the building design and that the warning system design is prepared by a professional engineer per CAN/ULC S540 and the Ontario Fire Code.

---

### Requirement 9: Heritage and Special Overlay Detection

**User Story:** As a permit applicant, I want the system to identify special zoning overlays, so that additional restrictions are not overlooked.

#### Acceptance Criteria

1. WHEN a property is in a heritage conservation district, THE System SHALL identify the Heritage_Overlay designation.
2. WHEN special zoning overlays apply (including ravine protection, flood plain, or utility easements), THE System SHALL identify the additional restrictions.
3. THE System SHALL reference the specific by-law or designation that creates the overlay.
4. WHEN a heritage overlay is detected, THE System SHALL flag that additional approvals may be required and that these typically extend the permit timeline.

---

### Requirement 10: Pre-Approved Plan Verification

**User Story:** As a permit applicant, I want the system to verify my use of a pre-approved plan, so that I can leverage standardized designs correctly.

#### Acceptance Criteria

1. WHERE a pre-approved plan number is provided, THE System SHALL verify that the plan applies to the property's zoning designation.
2. WHERE a pre-approved plan is referenced, THE System SHALL identify which compliance elements are covered by the pre-approved plan and which remain site-specific (including lot grading, tree protection, servicing, fire access path, and setbacks).
3. WHEN site-specific deviations from a pre-approved plan are detected, THE System SHALL identify the specific differences.
4. THE System SHALL reference the pre-approved plan documentation in its analysis and note that the pre-approved plan number should be cited in the permit application.

---

### Requirement 11: Clarifying Questions

**User Story:** As a permit applicant, I want the system to ask me clarifying questions, so that ambiguities are resolved before generating the response.

#### Acceptance Criteria

1. WHEN the System cannot determine information from uploaded documents, THE System SHALL generate specific clarifying questions for the user.
2. THE System SHALL present all clarifying questions before proceeding to response generation.
3. WHEN a user provides answers to clarifying questions, THE System SHALL incorporate the answers into its analysis.
4. THE System SHALL limit clarifying questions to information that cannot be reasonably inferred from the documents.
5. THE System SHALL include the following as standard clarifying questions when the information is not present in the uploaded documents:
   - "Does your property abut a public laneway? If so, what is the length of the abutting lot line?"
   - "What is your lot frontage dimension?"
   - "Are there any City-regulated trees within 6 m of the proposed footprint, including on neighbouring properties?"
   - "Do you have a current legal survey of the property?"
   - "Is your property subject to any heritage conservation district designation?"

---

### Requirement 12: Response Package Generation

**User Story:** As a permit applicant, I want the system to generate a complete response package, so that I can resubmit my permit application.

#### Acceptance Criteria

1. THE System SHALL generate a written response addressing each deficiency identified in the Examiner's Notice.
2. THE Citation_Generator SHALL include accurate regulatory citations for each response item.
3. THE System SHALL organize the response in the same order as the Examiner's Notice deficiencies.
4. THE System SHALL identify which deficiencies are resolved, which require drawing revisions, and which require variances or additional approvals.
5. THE Resubmission_Package SHALL include a summary of all changes made to address deficiencies.
6. THE System SHALL format the response package as a professional document suitable for submission to the City.
7. THE System SHALL include revision bubble annotations indicating where changes were made in the architectural drawings, consistent with City resubmission guidelines.
8. THE System SHALL note that only revised pages should be resubmitted (unchanged pages should not be included).
9. THE System SHALL include a professional cover letter summarizing the corrections and referencing the permit application number.

---

### Requirement 13: Regulatory Citation Accuracy

**User Story:** As a permit applicant, I want all regulatory citations to be accurate, so that my response is credible and professionally sound.

#### Acceptance Criteria

1. THE Citation_Generator SHALL reference the correct by-law number and section for all zoning citations (e.g., "Toronto Zoning By-law 569-2013, Section 150.8.60.1").
2. THE Citation_Generator SHALL reference the correct OBC division, part, section, and article for all building code citations (e.g., "Ontario Building Code, Division B, Section 9.10.20.3").
3. THE System SHALL verify that cited regulations are current and have not been superseded by more recent amendments.
4. WHEN a regulation has been amended, THE System SHALL reference the current version and identify the amending by-law (e.g., By-law 847-2025).
5. THE Citation_Generator SHALL include the full citation format including any applicable Ontario Regulation numbers (e.g., "Ontario Regulation 462/24, Section X").
6. THE System SHALL distinguish between provisions that are in full force and effect and those that remain under appeal at the Ontario Land Tribunal.

---

### Requirement 14: Knowledge Base Management

**User Story:** As a system administrator, I want the regulatory knowledge base to be maintainable, so that the system remains current with regulatory changes.

#### Acceptance Criteria

1. THE Knowledge_Base SHALL store all regulatory documents in a structured format.
2. THE Knowledge_Base SHALL organize documents by category: zoning, building code, city guidelines, tree protection, fire access, permit process, and templates.
3. THE System SHALL retrieve relevant regulatory sections based on the deficiency type.
4. THE Knowledge_Base SHALL support versioning of regulatory documents with effective dates.
5. WHEN a regulatory document is updated, THE System SHALL use the most current version for new analyses and retain prior versions for reference.
6. THE Knowledge_Base SHALL include the following minimum content (approximately 29 reference files):
   - Zoning: By-law 569-2013 Sections 150.7 and 150.8, By-laws 101-2022, 1107-2021, 847-2025, 849-2025, O. Reg. 462/24, residential zone regulations, former municipal by-law index.
   - Building Code: OBC Part 9, fire protection, plumbing (Section 7), structural, energy efficiency.
   - City guidelines: Fire access (garden suite and laneway suite variants), pre-approved plan catalog, electronic submission guidelines, ZALC requirements, development charges exemptions.
   - Tree protection: Chapter 813, arborist report standards, Urban Forestry guidelines.
   - Permit process: House Stream review, Examiner's Notice formats, deficiency categories, resubmission procedures.
   - Templates: Response package template, cover letter template.

---

### Requirement 15: Processing Performance

**User Story:** As a permit applicant, I want the system to process my submission quickly, so that I can meet resubmission deadlines.

#### Acceptance Criteria

1. THE System SHALL generate a complete response package within 5 minutes of receiving all required inputs for a typical submission (10-item Examiner's Notice with a 20-page plan set).
2. WHEN processing time exceeds 5 minutes, THE System SHALL provide a status update to the user indicating progress and estimated remaining time.
3. THE Orchestrator SHALL coordinate AI agents efficiently to minimize total processing time.
4. THE System SHALL process document uploads within 30 seconds of file submission.

---

### Requirement 16: Suite Type Routing

**User Story:** As a permit applicant, I want the system to apply the correct rules for my suite type, so that Garden Suite and Laneway Suite requirements are properly distinguished.

#### Acceptance Criteria

1. WHEN the suite type is Garden Suite, THE System SHALL apply the following garden-suite-specific rules:
   - Footprint: lesser of 60 m² or 40% of the rear yard.
   - Fire access path: minimum 1.0 m wide from the fronting public street.
   - Access must originate from the street the existing house faces.
   - Soft landscaping: at least 50% of the rear yard must remain permeable.
2. WHEN the suite type is Laneway Suite, THE System SHALL apply the following laneway-suite-specific rules:
   - Footprint: maximum 10.0 m × 8.0 m.
   - Lot must abut a public laneway by at least 3.5 m.
   - Fire access path: minimum 0.9 m wide; principal entrance on the laneway side.
   - Lot coverage: maximum 30%.
   - Soft landscaping: 60% of area between main house and suite for lots ≤6 m frontage; 85% for lots >6 m frontage (excluding permitted 1.5 m walkway).
   - Bicycle parking: minimum 2 spaces required.
   - No vehicle parking spaces required.
3. THE System SHALL apply different setback requirements based on suite type as specified in Requirement 5.
4. THE System SHALL apply different fire access path requirements based on suite type as specified in Requirement 6.
5. WHEN suite type affects zoning compliance, THE System SHALL clearly identify the suite-specific requirements and their by-law source.

---

### Requirement 17: Former Municipal Zoning Detection

**User Story:** As a permit applicant, I want the system to identify when former municipal zoning applies, so that pre-amalgamation rules are correctly handled.

#### Acceptance Criteria

1. WHEN a property is subject to former municipal zoning, THE System SHALL identify the legacy municipality (former City of Toronto, North York, Etobicoke, Scarborough, York, or East York).
2. WHEN former municipal zoning applies to a garden suite application, THE System SHALL flag that By-law 101-2022 does not apply and that the applicant should contact Toronto Building at 416-397-5330.
3. THE System SHALL reference the specific former by-law that applies to the property.
4. THE System SHALL clearly state that automated compliance validation is not available for properties under former municipal zoning in the MVP release.

---

### Requirement 18: Variance Trigger Identification

**User Story:** As a permit applicant, I want the system to identify when a variance is needed, so that I can pursue the appropriate approval process.

#### Acceptance Criteria

1. WHEN a zoning requirement cannot be met by the submitted design, THE System SHALL identify that a minor variance application to the Committee of Adjustment may be required.
2. THE System SHALL specify which zoning provision requires the variance.
3. THE System SHALL calculate the magnitude of the variance required (e.g., "side setback variance of 0.3 m requested; 0.3 m provided where 0.6 m is required").
4. THE System SHALL distinguish between minor variances (Committee of Adjustment, typically 3–6 months) and situations requiring rezoning (City Council).
5. THE System SHALL identify common variance triggers specific to Toronto laneway and garden suites: mature tree protection zones, unusual lot widths, tight separation distances, heritage overlays, and existing structures that exceed maximum footprint dimensions.

---

### Requirement 19: Professional Liability Disclaimer

**User Story:** As a system operator, I want to include appropriate disclaimers, so that users understand the system provides guidance but not professional certification.

#### Acceptance Criteria

1. THE System SHALL display a disclaimer that the response package is AI-generated and does not constitute professional engineering, architectural, or legal certification.
2. THE System SHALL advise users to have their submissions reviewed by a licensed architect, professional engineer, or BCIN-qualified designer before resubmission.
3. THE System SHALL indicate that final compliance determination rests with City of Toronto building examiners.
4. THE System SHALL present the disclaimer before processing begins and include it in the generated Response_Package.

---

### Requirement 20: Bilingual Consideration

**User Story:** As a permit applicant, I want the system to handle bilingual requirements where they arise.

#### Acceptance Criteria

1. THE System SHALL provide interface text in English for the MVP release.
2. WHERE regulatory documents exist in both English and French (certain OBC provisions), THE Knowledge_Base SHALL store both versions.
3. THE System SHALL flag that bilingual support may be required for future releases.

---

### Requirement 21: Error Handling and Validation

**User Story:** As a permit applicant, I want clear error messages when something goes wrong, so that I can correct issues and resubmit.

#### Acceptance Criteria

1. WHEN a PDF file cannot be parsed, THE System SHALL return a descriptive error message indicating the parsing failure and suggesting the user verify the file is not corrupted.
2. WHEN required information is missing from uploaded documents, THE System SHALL identify the specific missing information.
3. WHEN the Vision_Service fails to process a drawing page, THE System SHALL request manual input for the affected measurements.
4. WHEN the Orchestrator encounters an agent failure, THE System SHALL log the error and provide a user-friendly message.
5. IF a critical service is unavailable, THEN THE System SHALL return an error message indicating the service outage.
6. WHEN the System cannot determine whether a property falls under By-law 569-2013 or a former municipal by-law, THE System SHALL ask the user to confirm and recommend consulting the City's Zoning By-law Interactive Map.

---

### Requirement 22: Agent Orchestration

**User Story:** As a system operator, I want AI agents to work together efficiently, so that complex analyses are completed accurately.

#### Acceptance Criteria

1. THE Orchestrator SHALL coordinate the execution sequence of specialized AI agents.
2. THE Orchestrator SHALL pass relevant context from one agent to the next in the workflow.
3. THE Orchestrator SHALL execute agents in Agent_Sandbox environments for isolation.
4. WHEN an agent requires input from another agent, THE Orchestrator SHALL manage the dependency.
5. THE Orchestrator SHALL aggregate results from all agents into the final Response_Package.
6. THE Orchestrator SHALL support the following minimum agent types: Blueprint Reader, Examiner Notice Parser, Zoning Classifier, Suite Type Router, Footprint Validator, Height Validator, Setback Analyzer, Fire Access Evaluator, Tree Protection Assessor, OBC Checker, Landscaping Validator, Regulatory Updater (live web search), and Response Drafter.

---

### Requirement 23: Audit Trail and Logging

**User Story:** As a system operator, I want to track system decisions and processing steps, so that I can troubleshoot issues and improve accuracy.

#### Acceptance Criteria

1. THE System SHALL log all document uploads with timestamps.
2. THE System SHALL log all regulatory citations generated with their source documents.
3. THE System SHALL log all AI agent decisions and their reasoning.
4. THE System SHALL log all clarifying questions asked and user responses received.
5. THE System SHALL maintain logs for a minimum of 90 days.

---

### Requirement 24: Round-Trip Document Processing

**User Story:** As a system operator, I want to ensure document parsing accuracy, so that information is not lost or corrupted during processing.

#### Acceptance Criteria

1. THE PDF_Processor SHALL extract text content from PDF documents.
2. THE PDF_Processor SHALL preserve the original PDF structure and formatting.
3. FOR ALL successfully parsed documents, THE System SHALL verify that extracted content matches the original document structure.
4. WHEN text extraction fails for a section, THE System SHALL flag the section for manual review.

---

### Requirement 25: MVP Scope Boundaries

**User Story:** As a product manager, I want clear MVP scope boundaries, so that the initial release focuses on core functionality.

#### Acceptance Criteria

**Included in MVP:**

1. THE System SHALL support Garden Suite and Laneway Suite permit corrections under By-law 569-2013.
2. THE System SHALL support Examiner's Notice parsing and deficiency extraction.
3. THE System SHALL support zoning compliance validation including footprint, height, setbacks, separation, lot coverage, and landscaping.
4. THE System SHALL support Ontario Regulation 462/24 application for qualifying properties.
5. THE System SHALL support fire access path validation with suite-type-specific rules.
6. THE System SHALL support tree protection flagging and arborist report recommendations.
7. THE System SHALL support basic OBC Part 9 compliance checking.
8. THE System SHALL support heritage overlay and special zoning detection.
9. THE System SHALL support response package generation with accurate regulatory citations.
10. THE System SHALL support professional liability disclaimers.
11. THE System SHALL support Limiting Distance Agreement detection and flagging.

**Excluded from MVP:**

12. THE System SHALL exclude former municipal by-law full compliance validation from the MVP release (detection and flagging only).
13. THE System SHALL exclude full pre-approved plan integration from the MVP release (basic reference only).
14. THE System SHALL exclude automated variance assessment from the MVP release (flagging and magnitude calculation only).
15. THE System SHALL exclude automated drawing markup from the MVP release.
16. THE System SHALL exclude direct submission to the City's File Submission Hub API from the MVP release.
17. THE System SHALL exclude multi-user collaboration features from the MVP release.
18. THE System SHALL exclude GTA expansion (Mississauga, Vaughan, Richmond Hill, Durham) from the MVP release.

---

### Requirement 26: Servicing and Utilities Compliance

**User Story:** As a permit applicant, I want the system to flag servicing issues, so that utility connections comply with OBC and City requirements.

#### Acceptance Criteria

1. THE Servicing_Validator SHALL verify that the plans show routing for water, sanitary, storm, hydro, and gas connections to the suite.
2. THE Servicing_Validator SHALL flag the OBC plumbing separation rule (7.1.2.4(2)) when plumbing for the suite is connected to the services of the main building.
3. WHEN the plans do not show servicing routes, THE System SHALL flag this as a likely deficiency item.
4. THE System SHALL note that some sites may require lateral upgrades or a sump connection strategy and recommend confirming with the City.

---

### Requirement 27: Soft Landscaping and Site Coverage Validation

**User Story:** As a permit applicant, I want the system to verify landscaping requirements, so that my site plan meets rear-yard coverage and soft landscaping rules.

#### Acceptance Criteria

1. FOR Laneway Suites on lots with greater than 6 m frontage, THE Landscaping_Validator SHALL verify that at least 85% of the area between the rear main wall of the residence and the front main wall of the laneway suite is soft landscaping, excluding a permitted walkway up to 1.5 m wide.
2. FOR Laneway Suites on lots with 6 m or less frontage, THE Landscaping_Validator SHALL verify that at least 60% of the same area is soft landscaping.
3. FOR Garden Suites, THE Landscaping_Validator SHALL verify that at least 50% of the rear yard remains permeable.
4. WHEN soft landscaping requirements are not met, THE System SHALL identify the deficiency and cite the applicable By-law 569-2013 section.

---

### Requirement 28: Limiting Distance Agreement Detection

**User Story:** As a permit applicant, I want the system to identify when a Limiting Distance Agreement is needed, so that I can begin the legal process early.

#### Acceptance Criteria

1. WHEN the fire access path width cannot be achieved entirely within the applicant's property, THE System SHALL flag that a Limiting Distance Agreement with the neighbouring property owner is required.
2. THE System SHALL describe the LDA process: downloading the City's template agreement, retaining a lawyer, registering the agreement on title, and providing a title opinion.
3. THE System SHALL note that the LDA must be in place before submitting the building permit application.
4. THE System SHALL note that the LDA is an obligation that cannot be broken without the consent of all parties, including the City.

---

## MVP Scope Summary

The MVP release focuses on the core permit correction workflow for properties zoned under By-law 569-2013:

- Document upload and ingestion (architectural plans and Examiner's Notice up to 250 MB)
- Property information collection including address, suite type, and laneway abutment
- Examiner's Notice parsing with deficiency categorization
- Architectural plan analysis using AI vision
- Toronto Zoning By-law 569-2013 compliance validation (Section 150.7 for Garden Suites, Section 150.8 for Laneway Suites)
- Ontario Regulation 462/24 application for qualifying properties (≤3 units)
- Suite-type-specific fire access path validation (1.0 m garden / 0.9 m laneway)
- Tree protection assessment and arborist report flagging
- Basic OBC Part 9 compliance checking including plumbing separation
- Soft landscaping and site coverage validation
- Servicing route flagging
- Limiting Distance Agreement detection
- Heritage overlay and special zoning detection
- Variance trigger identification (flagging and magnitude only)
- Response package generation with accurate regulatory citations
- Professional liability disclaimers

**Future phases:**

- **Phase 2:** Former municipal by-law full compliance, complete pre-approved plan integration, automated variance assessment, Committee of Adjustment process guidance, GTA expansion
- **Phase 3:** Full OBC Part 9 automation (structural, mechanical, energy), automated drawing markup with revision bubbles, direct City File Submission Hub integration, multi-user collaboration and version tracking

---

## Technical Architecture Context

While implementation details belong in the design phase, the requirements assume:

- Frontend capable of PDF upload (up to 250 MB), property information input, and interactive clarifying question workflow
- Backend orchestration service coordinating 13 specialized AI agents
- AI vision service (Claude Opus) for reading architectural plans and Examiner's Notices page by page
- Isolated agent sandboxes for each skill execution
- Live web search capability for regulatory updates, Council decisions, and Ontario Land Tribunal rulings
- Knowledge base with ~29 structured reference files organized by regulatory category
- Document storage for user uploads, session state, and generated response packages

---

## Key Risk Areas

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Fire access path failure | Most common rejection reason; narrow Toronto side yards frequently fail width or travel-distance rules | Suite-type-specific validation (1.0 m garden / 0.9 m laneway); LDA detection; 90 m extended distance option with fire-safety measures |
| Tree protection conflicts | Protected trees (including on neighbouring lots) can force project redesigns; fines up to $100,000 per tree | Early TPZ flagging; arborist report recommendation; footprint-shaping guidance |
| Former municipal zoning | Properties under legacy by-laws are not covered by garden suite provisions in By-law 101-2022 | Address-based detection; explicit user notification; referral to Toronto Building (416-397-5330) |
| Pre-approved plan misapplication | Builders assume pre-approved plans eliminate all review; site-specific items still require compliance | Clear separation of covered vs. site-specific items |
| Angular plane ambiguity | O. Reg. 462/24 eliminates the requirement but City may still apply constraints in certain cases | Flag as nuance; recommend confirmation with examiner |
| Heritage overlay restrictions | Additional approvals add months to the timeline | Early detection; explicit flagging of extended process |
| O. Reg. 462/24 unit count limit | Regulation does not apply to properties with more than 3 residential units | Verify unit count before applying regulation provisions |
| Stale regulatory data | By-laws are actively being amended (2025 amendments ongoing) | Live web search agent supplements static knowledge base; version dating on all reference files |
| Vision extraction errors | AI may misread dimensions or miss annotations on complex architectural drawings | Confidence scoring; manual input fallback for low-confidence extractions; clarifying questions |