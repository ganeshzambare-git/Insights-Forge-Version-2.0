'use client';

import React, { useEffect } from 'react';
import { useResourceIsLoading, useResourceError, useResourceActions } from '../store/resourceAllocationStore';
import { AllocationFilters } from './AllocationFilters';
import { FinancialSummary } from './FinancialSummary';
import { ResourceUtilizationCards } from './ResourceUtilizationCards';
import { BudgetLedgerTable } from './BudgetLedgerTable';
import styles from './ResourceAllocationPage.module.css';

export const ResourceAllocationPage: React.FC = () => {
  const isLoading = useResourceIsLoading();
  const error = useResourceError();
  const { fetchResourceAllocation } = useResourceActions();

  useEffect(() => {
    fetchResourceAllocation();
  }, [fetchResourceAllocation]);

  return (
    <main className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Infrastructure & Financial Dashboard</h1>
          <p className={styles.pageSubtitle}>
            Tenant-scoped budget allocations, resource utilization, and financial summaries.
          </p>
        </div>
      </header>

      <AllocationFilters />
      <FinancialSummary />
      <ResourceUtilizationCards />

      {isLoading && (
        <div className={styles.statusRow} role="status" aria-live="polite">
          <span className={styles.spinner} aria-hidden="true" />
          Loading resource allocation data…
        </div>
      )}
      {error && !isLoading && (
        <div className={styles.errorBanner} role="alert">
          <strong>Error:</strong> {error}
          <button className={styles.retryBtn} onClick={fetchResourceAllocation}>Retry</button>
        </div>
      )}

      {!isLoading && !error && <BudgetLedgerTable />}
    </main>
  );
};
