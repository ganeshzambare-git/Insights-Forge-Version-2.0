import { create } from 'zustand';

interface GradeState {
  gradeValue: string;
  validationError: string | null;
  isSubmitting: boolean;
  submitSuccess: boolean;
  actions: {
    setGradeValue: (value: string) => void;
    formatGradeValue: () => void;
    submitGrade: () => Promise<void>;
    resetGradeStore: () => void;
  };
}

const useGradeStoreInternal = create<GradeState>((set, get) => ({
  gradeValue: '',
  validationError: null,
  isSubmitting: false,
  submitSuccess: false,
  actions: {
    setGradeValue: (gradeValue) => {
      set({ gradeValue, submitSuccess: false });
      const trimmed = gradeValue.trim();
      if (!trimmed) {
        set({ validationError: 'Grade value is required.' });
        return;
      }
      const val = parseFloat(trimmed);
      if (isNaN(val)) {
        set({ validationError: 'Grade must be a valid numeric decimal.' });
        return;
      }
      if (val > 100.00) {
        set({ validationError: 'Value exceeds absolute institutional ledger scale bounds (Max: 100.00).' });
        return;
      }
      if (val < 0.0) {
        set({ validationError: 'Grade value cannot be negative.' });
        return;
      }
      set({ validationError: null });
    },
    formatGradeValue: () => {
      const { gradeValue, validationError } = get();
      if (validationError || !gradeValue.trim()) return;
      const val = parseFloat(gradeValue.trim());
      if (!isNaN(val)) {
        set({ gradeValue: val.toFixed(2) });
      }
    },
    submitGrade: async () => {
      const { gradeValue, validationError } = get();
      if (validationError || !gradeValue.trim()) return;
      set({ isSubmitting: true });
      await new Promise((resolve) => setTimeout(resolve, 800));
      set({ isSubmitting: false, submitSuccess: true, gradeValue: '' });
    },
    resetGradeStore: () => {
      set({ gradeValue: '', validationError: null, isSubmitting: false, submitSuccess: false });
    }
  }
}));

export const useGradeValue = () => useGradeStoreInternal((s) => s.gradeValue);
export const useGradeValidationError = () => useGradeStoreInternal((s) => s.validationError);
export const useGradeIsSubmitting = () => useGradeStoreInternal((s) => s.isSubmitting);
export const useGradeSubmitSuccess = () => useGradeStoreInternal((s) => s.submitSuccess);
export const useGradeActions = () => useGradeStoreInternal((s) => s.actions);
