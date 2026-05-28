# DECISIONS.md — Architectural Resolutions & Assumptions

This document lists the systemic ambiguities identified within the project specification, the selected engineering resolutions, and the targeted discovery queries reserved for Product Management.

---

## 1. Boundary Scoping: Handled Scenarios vs. Excluded Edge Cases

### A. SAP Fuel Ledger Ingestion

* **What We Handled:** Structured CSV file extraction reflecting flat-file tabular formats exported via an OData endpoint or SAP BAPI. Cryptic SAP database abbreviations (`MBLNR` for Material Document, `WERKS` for Plant Code, `MENGE` for Quantity, `MEINS` for Unit) were completely mapped and successfully normalized.
* **What We Ignored:** Multi-currency currency conversion exchange-rate lookups (we flagged missing currencies but assumed base USD valuation tracking for calculations) and native IDoc parsing architectures due to processing time box limits.

### B. Utility Grid Electricity Ingestion

* **What We Handled:** Multi-line portal tabular exports containing billing cycles spanning custom dates, negative values, and varying unit layouts.
* **What We Ignored:** Automatic extraction of embedded tabular matrix strings from unstructured multi-page billing PDFs. We assumed utility data arrives as a structured CSV portal extraction.

### C. Corporate Travel Expenses

* **What We Handled:** Real-time JSON webhook arrays delivering geographical destination pairs (Airport-to-Airport metadata blocks like `JFK-LHR`).
* **What We Ignored:** Complex multimodal multi-leg multi-passenger layover allocations. Ground transit tracking was minimized to fixed default distance assumptions if route indicators were completely omitted.

---

## 2. Technical Ambiguities Resolved

### A. Data Resilience Strategy (Crashing vs. Flagging)

* **Ambiguity:** Should an ingestion payload with corrupted schemas cause the thread to crash out, or save with warning markers?
* **Resolution:** Built a validation-interception layer. Records processing corrupted schemas bypass standard automated `APPROVED` states, receive precise structural logging tags inside a `data_quality_flags` database cell array, and route immediately to the `PENDING_REVIEW` view on the React interface.

### B. Non-Calendar Billing Horizon Normalization

* **Ambiguity:** Utility bills regularly cross clean monthly parameters (e.g., January 15 to February 14).
* **Resolution:** Designed a time-weighted proration calculation. The pipeline computes aggregate elapsed days, determines average daily usage value quotients, and distributes calculated carbon parameters to specific target disclosure balance sheets based on active calendar weights.

---

## 3. Product Management Discovery Questionnaire

1. **Correction Workflows:** When an analyst rejects an ingestion line item, do they expect immediate inline grid editing capabilities inside our application, or does the pipeline trigger a workspace rejection note to the original client operations upload desk?
2. **Audit Locking Constrains:** Once an operational supervisor locks an ingestion run for external auditing, should subsequent corrections be completely restricted by hard database schema constraints, or can a high-privilege superuser override entries by generating an append-only compensating journal entry?
3. **Emission Factor Versioning:** Does the product require point-in-time mapping tables to recalculate history when reporting standard agencies (e.g., DEFRA, EPA) alter regional electrical grid intensity grid indices mid-year?
