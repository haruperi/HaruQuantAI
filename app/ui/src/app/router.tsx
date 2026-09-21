import { useEffect, useRef } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import type { ModuleId, ProjectTab } from './types';
import { useAppStore } from './store';

export const MODULE_ROUTES: Record<ModuleId, string> = {
  home: '/',
  datamanager: '/datamanager',
  business: '/business',
  builder: '/builder',
  algowizard: '/algowizard',
  codeeditor: '/codeeditor',
  neuralnet: '/neuralnet',
  retester: '/retester',
  optimizer: '/optimizer',
  mtanalyzer: '/mtanalyzer',
  projects: '/projects',
  portfolio: '/portfolio',
  composer: '/composer',
  trading: '/trading',
  debugconsole: '/debugconsole',
  gridcontrol: '/gridcontrol',
};

const TAB_CAPABLE_MODULES: ModuleId[] = ['builder', 'retester', 'optimizer', 'projects'];

/**
 * Resolves a URL pathname to the corresponding ModuleId, or null if unknown.
 */
export function getModuleFromPath(pathname: string): ModuleId | null {
  const normalized = pathname.replace(/\/+$/, '') || '/';
  if (normalized === '/' || normalized === '/home') return 'home';

  const entry = Object.entries(MODULE_ROUTES).find(([_, path]) => {
    if (path === '/') return false;
    return path === normalized || normalized.startsWith(`${path}/`);
  });

  return entry ? (entry[0] as ModuleId) : null;
}

/**
 * Returns the canonical URL path for a given ModuleId.
 */
export function getPathForModule(module: ModuleId): string {
  return MODULE_ROUTES[module] ?? '/';
}

/**
 * Two-way synchronization hook between React Router (URL pathname & query params)
 * and the Zustand application store.
 */
export function useRouteSync() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const storeModule = useAppStore((s) => s.module);
  const storeTab = useAppStore((s) => s.tab);
  const storeStrategyId = useAppStore((s) => s.selectedStrategyId);
  const storeBankId = useAppStore((s) => s.selectedBankId);

  const setModule = useAppStore((s) => s.setModule);
  const setTab = useAppStore((s) => s.setTab);
  const selectStrategy = useAppStore((s) => s.selectStrategy);
  const setBank = useAppStore((s) => s.setBank);

  const isSyncingInboundRef = useRef(false);

  // 1. INBOUND: URL -> Zustand Store
  useEffect(() => {
    isSyncingInboundRef.current = true;
    try {
      const resolvedModule = getModuleFromPath(location.pathname);
      if (resolvedModule && resolvedModule !== storeModule) {
        setModule(resolvedModule);
      }

      // Check tab query parameter
      const tabParam = searchParams.get('tab') as ProjectTab | null;
      if (tabParam && ['progress', 'settings', 'results'].includes(tabParam) && tabParam !== storeTab) {
        setTab(tabParam);
      }

      // Check strategyId query parameter
      const stratParam = searchParams.get('strategyId');
      if (stratParam !== null && stratParam !== storeStrategyId) {
        selectStrategy(stratParam);
      }

      // Check bankId query parameter
      const bankParam = searchParams.get('bankId');
      if (bankParam !== null && bankParam !== storeBankId) {
        setBank(bankParam);
      }
    } finally {
      // Delay releasing inbound flag to prevent immediate outbound echo in the same tick
      setTimeout(() => {
        isSyncingInboundRef.current = false;
      }, 0);
    }
  }, [location.pathname, searchParams, setModule, setTab, selectStrategy, setBank]);

  // 2. OUTBOUND: Store Module -> URL Path
  useEffect(() => {
    if (isSyncingInboundRef.current) return;
    const currentModule = getModuleFromPath(location.pathname);
    if (storeModule && currentModule !== storeModule) {
      const targetPath = getPathForModule(storeModule);
      const currentQuery = location.search;
      navigate(`${targetPath}${currentQuery}`, { replace: false });
    }
  }, [storeModule, location.pathname, location.search, navigate]);

  // 3. OUTBOUND: Store Tab -> Query Parameter
  useEffect(() => {
    if (isSyncingInboundRef.current) return;
    if (!TAB_CAPABLE_MODULES.includes(storeModule)) return;

    const currentTab = searchParams.get('tab');
    if (storeTab && currentTab !== storeTab) {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set('tab', storeTab);
          return next;
        },
        { replace: true }
      );
    }
  }, [storeTab, storeModule, searchParams, setSearchParams]);

  // 4. OUTBOUND: Store Strategy Selection -> Query Parameter
  useEffect(() => {
    if (isSyncingInboundRef.current) return;
    const currentStrat = searchParams.get('strategyId');
    if (storeStrategyId && currentStrat !== storeStrategyId) {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set('strategyId', storeStrategyId);
          return next;
        },
        { replace: true }
      );
    } else if (!storeStrategyId && currentStrat !== null) {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.delete('strategyId');
          return next;
        },
        { replace: true }
      );
    }
  }, [storeStrategyId, searchParams, setSearchParams]);
}

/**
 * Convenient navigation helper providing type-safe module navigation with query parameters.
 */
export function useAppNavigate() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  return {
    navigate,
    navigateTo: (module: ModuleId, extraParams?: Record<string, string>) => {
      const path = getPathForModule(module);
      const params = new URLSearchParams(searchParams);
      if (extraParams) {
        Object.entries(extraParams).forEach(([k, v]) => {
          if (v === '' || v === undefined || v === null) {
            params.delete(k);
          } else {
            params.set(k, v);
          }
        });
      }
      const qs = params.toString();
      navigate(qs ? `${path}?${qs}` : path);
    },
  };
}
