import { create } from 'zustand';

// ── Types ───────────────────────────────────────────────────
export interface BudgetLedgerEntry {
  allocation_id: string;
  category: string;
  description: string;
  allocated_budget: number;
  current_balance: number;
  utilization_pct: number;
  fiscal_year: string;
  dimension: string;
}

export interface UtilizationCard {
  label: string;
  value: string;
  icon: string;
  color: string;
}

export interface FinancialSummaryData {
  total_allocated: number;
  total_balance: number;
  total_spent: number;
  overall_utilization_pct: number;
  fiscal_year: string;
  tenant_id: string;
  generated_at: string;
}

interface ResourceAllocationState {
  budgetLedger: BudgetLedgerEntry[];
  utilizationCards: UtilizationCard[];
  financialSummary: FinancialSummaryData | null;
  selectedDimension: string;
  isLoading: boolean;
  error: string | null;
  actions: {
    fetchResourceAllocation: () => Promise<void>;
    setDimension: (dimension: string) => void;
  };
}

const useResourceAllocationStoreInternal = create<ResourceAllocationState>((set, get) => ({
  budgetLedger: [],
  utilizationCards: [],
  financialSummary: null,
  selectedDimension: '',
  isLoading: false,
  error: null,
  actions: {
    fetchResourceAllocation: async () => {
      set({ isLoading: true, error: null });
      try {
        const { selectedDimension } = get();
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const params = new URLSearchParams();
        if (selectedDimension) params.set('dimension', selectedDimension);

        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';
        const res = await fetch(
          `${apiUrl}/api/v1/finance/resource-allocation?${params.toString()}`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} }
        );

        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const json = await res.json();

        set({
          budgetLedger: json.data.budget_ledger ?? [],
          utilizationCards: json.data.utilization_cards ?? [],
          financialSummary: json.data.financial_summary ?? null,
          isLoading: false,
        });
      } catch (err: any) {
        set({ error: err.message ?? 'Failed to load resource allocation data.', isLoading: false });
      }
    },
    setDimension: (dimension) => {
      set({ selectedDimension: dimension });
    },
  },
}));

export const useBudgetLedger = () => useResourceAllocationStoreInternal((s) => s.budgetLedger);
export const useUtilizationCards = () => useResourceAllocationStoreInternal((s) => s.utilizationCards);
export const useFinancialSummary = () => useResourceAllocationStoreInternal((s) => s.financialSummary);
export const useSelectedDimension = () => useResourceAllocationStoreInternal((s) => s.selectedDimension);
export const useResourceIsLoading = () => useResourceAllocationStoreInternal((s) => s.isLoading);
export const useResourceError = () => useResourceAllocationStoreInternal((s) => s.error);
export const useResourceActions = () => useResourceAllocationStoreInternal((s) => s.actions);
