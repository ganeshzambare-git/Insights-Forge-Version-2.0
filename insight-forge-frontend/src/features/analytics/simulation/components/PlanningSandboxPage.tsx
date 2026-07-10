'use client';

import React, { useEffect } from 'react';
import {
  useCreditRatio,
  useTargetCohorts,
  useClassCapacity,
  useIsSandboxDirty,
  useSimulationLoading,
  useSimulationError,
  useSimulationSuccessRate,
  useSimulationAverageGpa,
  useSimulationTrend,
  useSimulationActions,
} from '../store/simulationStore';
import styles from './PlanningSandboxPage.module.css';

export const PlanningSandboxPage: React.FC = () => {
  const creditRatio = useCreditRatio();
  const targetCohorts = useTargetCohorts();
  const classCapacity = useClassCapacity();
  const isDirty = useIsSandboxDirty();
  const loading = useSimulationLoading();
  const error = useSimulationError();
  const successRate = useSimulationSuccessRate();
  const averageGpa = useSimulationAverageGpa();
  const trend = useSimulationTrend();
  const { setCreditRatio, setTargetCohorts, setClassCapacity, resetSandbox, runSimulation } = useSimulationActions();

  useEffect(() => {
    if (!isDirty) return;

    const delayDebounce = setTimeout(() => {
      runSimulation();
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [creditRatio, targetCohorts, classCapacity, isDirty, runSimulation]);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h2 className={styles.title}>Out-of-Band Academic Planner</h2>
          <p className={styles.subtitle}>Simulate institutional GPA shifts and cohort capacity trends safely (Dean-2 view)</p>
        </div>
        {isDirty && (
          <button onClick={resetSandbox} className={styles.resetBtn}>
            Reset Sandbox
          </button>
        )}
      </header>

      <div className={styles.splitGrid}>
        {/* Left Column: Sliders */}
        <section className={styles.controlsCard}>
          <h3 className={styles.sectionTitle}>Sandbox Parameters</h3>
          
          <div className={styles.controlGroup}>
            <label htmlFor="credit-ratio-input" className={styles.label}>
              Academic Credit Ratio: <strong>{creditRatio.toFixed(2)}</strong>
            </label>
            <input
              id="credit-ratio-input"
              type="range"
              min={0.1}
              max={1.0}
              step={0.05}
              value={creditRatio}
              onChange={(e) => setCreditRatio(parseFloat(e.target.value))}
              className={styles.slider}
              aria-valuemin={0.1}
              aria-valuemax={1.0}
              aria-valuenow={creditRatio}
            />
          </div>

          <div className={styles.controlGroup}>
            <label htmlFor="cohort-size-input" className={styles.label}>
              Target Cohorts Count: <strong>{targetCohorts}</strong>
            </label>
            <input
              id="cohort-size-input"
              type="range"
              min={1}
              max={50}
              step={1}
              value={targetCohorts}
              onChange={(e) => setTargetCohorts(parseInt(e.target.value, 10))}
              className={styles.slider}
              aria-valuemin={1}
              aria-valuemax={50}
              aria-valuenow={targetCohorts}
            />
          </div>

          <div className={styles.controlGroup}>
            <label htmlFor="capacity-input" className={styles.label}>
              Class Seats Capacity: <strong>{classCapacity}</strong>
            </label>
            <input
              id="capacity-input"
              type="range"
              min={10}
              max={150}
              step={5}
              value={classCapacity}
              onChange={(e) => setClassCapacity(parseInt(e.target.value, 10))}
              className={styles.slider}
              aria-valuemin={10}
              aria-valuemax={150}
              aria-valuenow={classCapacity}
            />
          </div>
        </section>

        {/* Right Column: Visualizer */}
        <section className={styles.visualizerCard}>
          <h3 className={styles.sectionTitle}>Simulated Projections</h3>

          {!isDirty ? (
            <div className={styles.emptyHint}>
              <div className={styles.hintIcon}>💡</div>
              <h4>Planning Sandbox Ready</h4>
              <p>Adjust simulation parameters on the left to begin exploring hypothetical planning models.</p>
            </div>
          ) : (
            <div className={styles.resultsWrapper}>
              {loading && <div className={styles.floatingLoader}>Recalculating...</div>}

              {error && (
                <div className={styles.errorAlert}>
                  <span>⚠️</span> {error}
                </div>
              )}

              {successRate !== null && averageGpa !== null && (
                <>
                  <div className={styles.statsGrid}>
                    <div className={styles.statBox}>
                      <div className={styles.statLabel}>Success Projection</div>
                      <div className={styles.statVal}>{successRate}%</div>
                    </div>
                    <div className={styles.statBox}>
                      <div className={styles.statLabel}>Projected Term GPA</div>
                      <div className={styles.statVal}>{averageGpa.toFixed(2)}</div>
                    </div>
                  </div>

                  {trend.length > 0 && (
                    <div className={styles.chartArea}>
                      <h4 className={styles.chartTitle}>GPA Growth Timeline</h4>
                      <svg viewBox="0 0 400 120" width="100%" height="120px" style={{ overflow: 'visible' }}>
                        <defs>
                          <linearGradient id="sandboxGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                          </linearGradient>
                        </defs>
                        <line x1="10" y1="20" x2="390" y2="20" stroke="rgba(255,255,255,0.05)" />
                        <line x1="10" y1="60" x2="390" y2="60" stroke="rgba(255,255,255,0.05)" />
                        <line x1="10" y1="100" x2="390" y2="100" stroke="rgba(255,255,255,0.1)" />

                        <path
                          d={`M 10 ${100 - (trend[0].gpa - 1) * 30} 
                             L 105 ${100 - (trend[1].gpa - 1) * 30} 
                             L 200 ${100 - (trend[2].gpa - 1) * 30} 
                             L 295 ${100 - (trend[3].gpa - 1) * 30} 
                             L 390 ${100 - (trend[4].gpa - 1) * 30}`}
                          fill="none"
                          stroke="#10b981"
                          strokeWidth="3"
                          strokeLinecap="round"
                        />

                        <path
                          d={`M 10 ${100 - (trend[0].gpa - 1) * 30} 
                             L 105 ${100 - (trend[1].gpa - 1) * 30} 
                             L 200 ${100 - (trend[2].gpa - 1) * 30} 
                             L 295 ${100 - (trend[3].gpa - 1) * 30} 
                             L 390 ${100 - (trend[4].gpa - 1) * 30}
                             L 390 100 L 10 100 Z`}
                          fill="url(#sandboxGrad)"
                        />

                        <circle cx="10" cy={100 - (trend[0].gpa - 1) * 30} r="4" fill="#020617" stroke="#10b981" strokeWidth="2" />
                        <circle cx="105" cy={100 - (trend[1].gpa - 1) * 30} r="4" fill="#020617" stroke="#10b981" strokeWidth="2" />
                        <circle cx="200" cy={100 - (trend[2].gpa - 1) * 30} r="4" fill="#020617" stroke="#10b981" strokeWidth="2" />
                        <circle cx="295" cy={100 - (trend[3].gpa - 1) * 30} r="4" fill="#020617" stroke="#10b981" strokeWidth="2" />
                        <circle cx="390" cy={100 - (trend[4].gpa - 1) * 30} r="4" fill="#020617" stroke="#10b981" strokeWidth="2" />
                      </svg>
                      <div className={styles.chartLabels}>
                        {trend.map((t) => (
                          <span key={t.step}>{t.step}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
