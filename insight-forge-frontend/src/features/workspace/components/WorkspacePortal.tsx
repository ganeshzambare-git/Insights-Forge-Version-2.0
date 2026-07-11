'use client';

import React from 'react';
import {
  useWorkspaceSlug,
  useWorkspaceLoading,
  useWorkspaceError,
  useWorkspaceActions,
} from '../store/workspaceStore';
import styles from './WorkspacePortal.module.css';

export const WorkspacePortal: React.FC = () => {
  const slug = useWorkspaceSlug();
  const loading = useWorkspaceLoading();
  const error = useWorkspaceError();
  const { setSlug, verifyWorkspace } = useWorkspaceActions();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSlug(e.target.value);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (slug.length > 3 && !loading) {
      await verifyWorkspace();
    }
  };

  const isInputInvalid = error !== null;

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h2 className={styles.title}>Access Your Workspace</h2>
        <p className={styles.subtitle}>Enter your institutional subdomain to verify identity</p>

        <form onSubmit={handleFormSubmit} className={styles.form} noValidate>
          <div className={styles.inputGroup}>
            <label htmlFor="workspace-slug" className={styles.label}>
              Workspace Address
            </label>
            <div className={styles.inputContainer}>
              <input
                id="workspace-slug"
                name="workspaceSlug"
                type="text"
                value={slug}
                onChange={handleInputChange}
                className={`${styles.input} ${isInputInvalid ? styles.inputError : ''}`}
                placeholder="university-name"
                disabled={loading}
                aria-invalid={isInputInvalid}
                aria-describedby={isInputInvalid ? "workspace-error" : undefined}
                required
              />
              <span className={styles.domainSuffix}>.insightforge.edu</span>
            </div>
            {isInputInvalid && (
              <span id="workspace-error" className={styles.errorText} role="alert">
                <span className={styles.errorIcon}></span> {error}
              </span>
            )}
          </div>

          <button
            type="submit"
            className={styles.button}
            disabled={slug.length <= 3 || loading}
          >
            {loading ? <span className={styles.spinner} aria-hidden="true" /> : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  );
};
