'use client';

import React from 'react';
import { useSelectedDimension, useResourceActions } from '../store/resourceAllocationStore';
import styles from './ResourceAllocationPage.module.css';

const DIMENSIONS = ['', 'Technology', 'Academic', 'Student Affairs', 'Research'];

export const AllocationFilters: React.FC = () => {
  const selectedDimension = useSelectedDimension();
  const { setDimension, fetchResourceAllocation } = useResourceActions();

  const handleChange = (value: string) => {
    setDimension(value);
  };

  const handleApply = () => fetchResourceAllocation();
  const handleClear = () => { setDimension(''); fetchResourceAllocation(); };

  return (
    <div className={styles.filterBar} role="search" aria-label="Resource allocation filters">
      <div className={styles.filterGroup}>
        <label htmlFor="dimension-filter" className={styles.filterLabel}>Organizational Dimension</label>
        <select
          id="dimension-filter"
          className={styles.filterSelect}
          value={selectedDimension}
          onChange={(e) => handleChange(e.target.value)}
          aria-label="Filter by organizational dimension"
        >
          {DIMENSIONS.map((d) => (
            <option key={d} value={d}>{d || 'All Dimensions'}</option>
          ))}
        </select>
      </div>

      <div className={styles.filterActions}>
        <button className={styles.applyBtn} onClick={handleApply} aria-label="Apply dimension filter">
          Apply
        </button>
        <button className={styles.clearBtn} onClick={handleClear} aria-label="Clear dimension filter">
          Clear
        </button>
      </div>
    </div>
  );
};
