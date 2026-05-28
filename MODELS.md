# MODEL.md — ESG Data Pipeline & Multi-Tenant Architecture

This document outlines the relational data model designed for the Breathe ESG Technical Ingestion Engine. The architecture prioritizes strict multi-tenancy, processing states, human-in-the-loop review capabilities, and an immutable audit trail.

---

## 1. Architectural Strategy & Entity Relationship Diagram

The core engine segregates data into three logical tiers:

1. **The Ingestion Plane (`DataIngestionRun`):** Tracks batch operations, source origins, and file uploads.
2. **The Staging/Staged Plane (`EmissionRecord`):** Acts as a polymorphic state-machine handling raw JSON data along with its normalized variants.
3. **The Governance Plane (`AuditLog`):** An immutable historical ledger tracking modifications, manual overwrites, and approval actions.

## 2. Schema Specification & Field Justification

### A. Model: `Organization`

The root entity facilitating multi-tenancy isolation. All subsequent data records must filter through an explicit or implicit organization scope.

* `id` (`UUIDField`, Primary Key): Prevents consecutive ID scanning attacks and provides robust multi-tenant security over integer keys.
* `name` (`CharField`, Unique): Human-readable name of the corporate enterprise client.

### B. Model: `DataIngestionRun`

Groups rows processed during a unique file ingestion event or webhook broadcast. This structure facilitates quick rollbacks, performance analytics, and lineage audits.

* `source_type` (`CharField`, Choices): Enforces systemic source origins: `SAP_PROCUREMENT`, `UTILITY_CSV`, or `CONCUR_TRAVEL`.
* `uploaded_at` (`DateTimeField`): Captures the point-in-time timestamp of transaction initiation.

### C. Model: `EmissionRecord`

The workhorse model. It maps unstable enterprise source properties to standardized carbon data types.

* `raw_payload` (`JSONField`): **Crucial Core Requirement.** Stores the exact, unmodified, raw data dictionary from the origin system. This guarantees data lineage and satisfies auditor inspection needs.
* `status` (`CharField`, Choices): Drives the data pipeline state machine: `STAGING` $\rightarrow$ `PENDING_REVIEW` $\rightarrow$ `APPROVED` / `REJECTED`.
* `data_quality_flags` (`JSONField`, Default=`[]`): A dynamic array storing strings detailing pipeline exceptions (e.g., `["SUSPICIOUS_HIGH_VALUE", "NON_CALENDAR_ALIGNED"]`). This structure directly drives UI formatting blocks.
* `normalized_quantity` & `normalized_unit`: Unified reporting properties (e.g., kWh for electricity, km for corporate transit flights).
* `co2_equivalent_tons` (`DecimalField`): The calculated environmental ledger metric ready for consolidated ESG disclosure sheets.

### D. Model: `AuditLog`

An append-only database collection tracking inline cell updates and analyst justification reasons.

* `previous_state` & `new_state` (`JSONField`): Captures before/after point-in-time attribute matrices for exact row delta tracking.
* `justification` (`TextField`): Mandatory textual logging entry detailing why a human analyst overrode an engine validation rule.

---

## 3. Scope 1 / 2 / 3 Categorization Mapping Logic

The ingestion handlers automatically tag Greenhouse Gas Protocol boundaries based on the architectural source stream:

* **SAP Fuel Ledger Ingestion** $\rightarrow$ Maps to **Scope 1 (Direct Combustion)** or **Scope 3 (Category 1: Purchased Goods and Services)** depending on cost center flags.
* **Utility Grid Electricity Ingestion** $\rightarrow$ Maps to **Scope 2 (Indirect Emissions from Purchased Energy)**.
* **Corporate Travel Expense Sync** $\rightarrow$ Maps to **Scope 3 (Category 6: Business Travel)**.

---

## 4. Multi-Tenancy Enforcement Mechanism

Data isolation is managed via an explicit ForeignKey relationship on the `Organization` schema. Every API router applies an implicit filter string (`.filter(organization=request.user.organization)`) ensuring that Client A can never run structural queries or intersect records belonging to Client B.
