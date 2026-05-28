# SOURCES.md — Real-World Data Domain Research

This document details the real-world operational profiles of the target systems, the insights gleaned during domain research, and specific structural edge cases designed into the data seed matrices.

---

## 1. System Source 1: SAP Enterprise Resource Planning (ERP)

* **Real-World Interface Protocol:** SAP ledger information is typically drawn either via scheduled background flat-file extractions (Application Server File System shares) or real-time OData REST endpoints mapping to SAP Financial Accounting (FI) and Materials Management (MM) ledgers.
* **Domain Realities & Insights:** Production SAP databases utilize cryptic German naming paradigms dating back decades. A core procurement tracking table will export headers like `MBLNR` instead of `Material_Document_Number`, `WERKS` instead of `Plant_Site`, and units like `MEINS`.
* **Sample Data Architecture & Failures:** We fabricated a 20-column layout replicating an SAP material ledger extract. Built-in system testing vectors include structural Excel equation dropouts (`#REF!`), European date layouts (`15.03.2024` vs ISO standard parameters), negative ledger adjustment items (`BSART` reversal identifiers), and string data type contaminations ("Five Hundred" in place of float parameters).

## 2. System Source 2: Utility Provider Invoices

* **Real-World Interface Protocol:** Energy records are gathered via commercial portal export spreadsheets (e.g., Pacific Gas & Electric, Consolidated Edison web exports) or automated EDI 810 transaction sets managed via sustainability operations networks.
* **Domain Realities & Insights:** Utility consumption tracking cycles rarely align with standardized Gregorian calendar boundaries. A physical reading event will track from December 14 to January 17, demanding chronological proration metrics to preserve true monthly baseline tracking accuracy.
* **Sample Data Architecture & Failures:** We constructed a dataset incorporating realistic grid usage characteristics (`Usage_Value`, `Unit_Of_Measure`, `Tariff_Code`). Testing parameters integrate non-calendar aligned windows, negative energy usage items, and unparseable billing text strings.

## 3. System Source 3: Corporate Travel Frameworks (Concur / Navan)

* **Real-World Interface Protocol:** Real-time webhooks dispatching JSON object notifications immediately following corporate card booking confirmation actions.
* **Domain Realities & Insights:** Enterprise expense feeds rarely output calculated flight mileage data rows. The incoming pipeline payload provides raw airport hub identifiers (e.g., `SFO`, `LHR`), demanding that consumer platforms maintain local geo-coordinate mapping tables to execute Haversine flight distance computations.
* **Sample Data Architecture & Failures:** Prepared an array format JSON collection tracking corporate route movements. Edge-case vectors incorporate unmapped or corrupt IATA airport designations (e.g., `UNK`), forcing the engine validation layer to trigger custom unmapped location flags on the React data view.

---

## 4. Operational Production Failure Analysis

If this system were pushed to a live global enterprise cloud stack today, the following components would experience immediate architectural distress:

1. **Airport DB Scaling:** The Haversine travel engine contains a static dictionary of 4 airport codes. It will throw unmapped location flags for any other corporate destination worldwide until linked to a real-time third-party IATA airport database API.
2. **Memory Overrun Vulnerabilities:** Large clients uploading half a million rows of historical procurement data could overwhelm server memory buffers due to our synchronous in-memory file parsing architecture. Transitioning to a background worker engine (Celery/Redis) would become mandatory.
3. **CORS and Network Routing Blocks:** If deployed across distributed cloud instances without precise white-listed domain parameters, cross-origin resource filters would prevent the React client from correctly querying the database ledger views.
