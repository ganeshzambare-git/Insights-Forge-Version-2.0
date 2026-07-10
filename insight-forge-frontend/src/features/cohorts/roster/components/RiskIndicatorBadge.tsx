import React from 'react';
import styles from './RiskIndicatorBadge.module.css';

interface RiskIndicatorBadgeProps {
  riskLevel?: string;
}

export const RiskIndicatorBadge: React.FC<RiskIndicatorBadgeProps> = ({ riskLevel }) => {
  const level = riskLevel || 'UnknownStatus';

  let badgeStyle = styles.neutralBadge;
  let labelText = 'Unknown Risk';
  let ariaLabel = 'Risk status: Unknown';

  switch (level.toLowerCase()) {
    case 'amber':
      badgeStyle = styles.amberBadge;
      labelText = 'At Risk';
      ariaLabel = 'Risk status: At Risk';
      break;
    case 'critical':
      badgeStyle = styles.criticalBadge;
      labelText = 'Critical';
      ariaLabel = 'Risk status: Critical';
      break;
    case 'normal':
      badgeStyle = styles.normalBadge;
      labelText = 'Normal';
      ariaLabel = 'Risk status: Normal';
      break;
    default:
      badgeStyle = styles.neutralBadge;
      labelText = level;
      ariaLabel = `Risk status: ${level}`;
      break;
  }

  return (
    <span 
      className={badgeStyle} 
      role="status" 
      aria-label={ariaLabel}
    >
      {labelText}
    </span>
  );
};
