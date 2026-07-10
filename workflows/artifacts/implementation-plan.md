# Implementation Plan - Phase 6 Data Integrity, Validation Constraints & Referential Safety

This plan details the implementation strategy for Tasks 22, 23, and 24 in the backend and frontend.

---

## User Review Required

> [!IMPORTANT]
> **FastAPI Endpoints**:
> - We will create `GET /api/v1/ingest/dead-letter-logs` in `app/api/v1/endpoints/ingest.py`.
> - We will create `DELETE /api/v1/cohorts/{cohort_id}` in `app/api/v1/endpoints/cohorts.py returning HTTP 409 Conflict with dependency information on conflict mock parameters.
> - **Grade Bounds Message**:
>   - Entering values above 100.00 will immediately display exactly:
>     `Value exceeds absolute institutional ledger scale bounds (Max: 100.00).`
> - **Referential safety conflict dialog**:
>   - Mismatch conflicts on cohort removals display exactly:
>     `An active institutional space or cohort tracking structure cannot be expunged while underlying operational records remain active.`

---

## Open Questions

- Should the grade validation formatter trigger formatting to two decimal places on blur or keypress? (Recommended: format to two decimals on input blur to preserve smooth typing transitions).

---

## Proposed Changes

### Backend: FastAPI Route Extensions
---
#### [MODIFY] [ingest.py](file:///d:/readynest/insight-forge-Version_2/insight-forge-Version_2/insight-forge-backend/app/api/v1/endpoints/ingest.py)
- Expose `GET /api/v1/ingest/dead-letter-logs` to query ingestion schema failures.

#### [MODIFY] [cohorts.py](file:///d:/readynest/insight-forge-Version_2/insight-forge-Version_2/insight-forge-backend/app/api/v1/endpoints/cohorts.py)
- Expose `DELETE /api/v1/cohorts/{cohort_id}`.

### Frontend Features: Tasks 22–24
---
#### [NEW] [gradeStore.ts](file:///d:/readynest/insight-forge-Version_2/insight-forge-Version_2/insight-forge-frontend/src/features/task22/store/gradeStore.ts)
- Zustand store tracking input states, grade errors, and submission status.

#### [NEW] [GradeEditor.tsx](file:///d:/readynest/insight-forge-Version_2/insight-forge-Version_2/insight-forge-frontend/src/features/task22/components/GradeEditor.tsx)
- Numerical entry field triggering ledger scale warning badges.

#### [NEW] [deadLetterStore.ts](file:///d:/readynest/insight-forge-Version_2/insight-forge-Version_2/insight-forge-frontend/src/features/task23/store/deadLetterStore.ts)
- Zustand store retrieving dead-letter logs.

#### [NEW] [DeadLetterPanel.tsx](file:///d:/readynest/insight-forge-Version_2/insight-forge-Version_2/insight-forge-frontend/src/features/task23/components/DeadLetterPanel.tsx)
- Administrator diagnostics interface with high-contrast warning elements.

#### [NEW] [deleteStore.ts](file:///d:/readynest/insight-forge-Version_2/insight-forge-Version_2/insight-forge-frontend/src/features/task24/store/deleteStore.ts)
- Zustand store managing cohort deletes and active dependencies.

#### [NEW] [DeleteConfirmationDialog.tsx](file:///d:/readynest/insight-forge-Version_2/insight-forge-Version_2/insight-forge-frontend/src/features/task24/components/DeleteConfirmationDialog.tsx)
- Dialog overlay rendering active referential conflict block warning paragraphs.

#### [MODIFY] [page.tsx](file:///d:/readynest/insight-forge-Version_2/insight-forge-Version_2/insight-forge-frontend/src/app/admin/page.tsx)
- Integrate new administrative features (Grade Editor, Ingestion Dead-letter Logs, Cohort Deletion Guards).

---

## Verification Plan

### Automated Tests
- Run backend unit tests (`pytest`).
- Validate Next.js build compilation (`npm run build`).

### Manual Verification
- Test Grade scale: Enter `105.50` and confirm warning badge displays exactly: `Value exceeds absolute institutional ledger scale bounds (Max: 100.00).` and disables submission.
- Test Dead-Letter Logs: Press refresh and confirm logs show files with missing headers.
- Test Deletion Conflict: Press delete cohort and verify the modal displays dependencies and blocks deletion.
