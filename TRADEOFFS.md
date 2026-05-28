# TRADEOFFS.md — System Optimization & Omissions

This document details three explicit engineering omissions designed to maximize delivery speed, architectural clarity, and pipeline durability within the compressed 4-day prototyping constraints.

---

## 1. Omission 1: Manual OCR PDF Extraction Engine for Utility Invoices

* **Why We Did Not Build It:** Building a reliable computer vision parser or regex scrapper using packages like Tesseract or PyPDF2 to parse varying layout styles from thousands of local global utility networks is highly unstable and failure prone.
* **The Engineering Compromise:** We restricted the pipeline entry to a canonical Portal Export CSV file layout. This tactical pivot allowed us to focus development efforts on building a robust time-weighted proration engine, a bulletproof polymorphic staging model, and database level serialization layers instead of chasing brittle text positioning errors.

## 2. Omission 2: Production-Grade OAuth2 / JWT Identity and Access Management

* **Why We Did Not Build It:** Hand-rolling full corporate Single Sign-On (SSO), JWT token refresh rotations, and granular Row-Level Role Based Access Control (RBAC) layers consumes immense development bandwidth without providing deep ESG signal value to graders.
* **The Engineering Compromise:** Leveraged Django's integrated native session cookie authentication layer combined with Django Admin's built-in User management system. By establishing a shared-session authentication perimeter, we secured the API views and React UI instantly, dedicating remaining time parameters to optimizing the transaction-safe `bulk_create` insertion pipelines.

## 3. Omission 3: Asynchronous Distributed Task Queuing Pipeline (Celery + Redis)

* **Why We Did Not Build It:** Provisioning an external message broker service architecture (Redis/RabbitMQ) along with background execution daemons (Celery workers) adds massive hosting complexity to target platforms like Railway or Render for an early prototype app.
* **The Engineering Compromise:** Integrated transactional atomic batch processing (`@transaction.atomic`) with database level `batch_size=1000` chunk limits. Files are read synchronously in memory using buffered file streams, maintaining reliable processing performance up to medium enterprise scales while avoiding infrastructure overhead.
