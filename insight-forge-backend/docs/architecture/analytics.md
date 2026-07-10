# Analytics & Business Intelligence Engine — Insight Forge V2

This document details the architecture, data models, algorithms, and design choices of the Analytics Engine.

---

## 1. Engine Architecture & Flow

To avoid introducing separate database tables or background processing worker nodes (preserving Render/Railway free-tier constraints), the Analytics Engine executes **synchronously** directly over the existing multi-tenant relational schema:

```
Client Request
      ↓
Analytics Router (RBAC check & get_current_user)
      ↓
Analytics Service (Business aggregations & Risk rules)
      ↓
PostgreSQL Query (SQL Window functions & Conditional cases)
```

---

## 2. Dynamic Risk Classification Algorithm

The Risk classification is computed deterministically in a stateless manner based on the following rules:

### A. Classification Status Levels:
1. **Critical**:
   - GPA (latest recorded metric) < `60.00` OR
   - Attendance Rate (latest recorded metric) < `75.00` OR
   - Total logged Critical Interventions (carrying the word `"critical"` in notes) $\ge 3$.
2. **Amber**:
   - GPA (latest recorded metric) < `75.00` OR
   - Attendance Rate (latest recorded metric) < `85.00` OR
   - Total logged Critical Interventions $\ge 1$.
3. **Safe**:
   - Evaluated otherwise (no triggers met, or student has no metrics logged).

---

## 3. SQL Aggregation & Performance Strategy

To ensure sub-second response times and prevent loading large numbers of rows into memory:
1. **Subqueries**: All latest student metrics are fetched using a grouping subquery selecting `MAX(metric_id)`.
2. **Single-Query Jointures**: Student details, latest GPA grades, attendance percentages, and critical intervention counts are resolved in a single consolidated outer-joined query.
3. **Ingress Trends**: Aggregate counts for interventions are processed using conditional case statements (`func.count(case((recorded_timestamp >= date, 1)))`) in a single query.
4. **Tenant Isolation**: Every database query strictly filters by `tenant_id` to enforce multitenancy.

---

## 4. Recommendation Engine Rules

We execute a local rule engine that evaluates metrics and logs:
- **Rule: CRITICAL_GPA / LOW_GPA**: Warns on GPA boundaries (<60 or <75) and recommends academic coaching.
- **Rule: CRITICAL_ATTENDANCE / LOW_ATTENDANCE**: Warns on attendance rates (<75% or <85%) and flags for parent/dean consult.
- **Rule: DEAN_REVIEW**: Triggers on any student currently evaluated in the `Critical` risk tier.
- **Rule: INTERVENTION_LAPSE**: Warns when a student is currently in `Amber` or `Critical` risk and has had no coaching interventions in the last 60 days.

---

## 5. Overall Institutional Health Score
Determined as a weighted index of student risk distributions:
$$\text{Health Score} = \frac{\text{SafeCount} \times 1.0 + \text{AmberCount} \times 0.6 + \text{CriticalCount} \times 0.1}{\text{TotalStudents}} \times 100$$
If `TotalStudents` is 0, defaults to `100.00`.
