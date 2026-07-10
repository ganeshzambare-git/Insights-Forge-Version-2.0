'use client';

import React from 'react';
import { useUtilizationCards } from '../store/resourceAllocationStore';
import styles from './ResourceAllocationPage.module.css';

export const ResourceUtilizationCards: React.FC = () => {
  const cards = useUtilizationCards();

  if (!cards.length) return null;

  return (
    <div className={styles.utilizationGrid} role="region" aria-label="Resource utilization summary">
      {cards.map((card) => (
        <div key={card.label} className={styles.utilizationCard}>
          <span className={styles.cardIcon} aria-hidden="true">{card.icon}</span>
          <span className={styles.cardValue} style={{ color: card.color }}>{card.value}</span>
          <span className={styles.cardLabel}>{card.label}</span>
        </div>
      ))}
    </div>
  );
};
