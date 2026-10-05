/** Startup discovery of local UI declarations; no hand-maintained feature list. */
import type { ComponentType, ReactNode } from 'react';

export interface NavigationContribution {
  readonly id: string;
  readonly path: string;
  readonly aliases?: readonly string[];
  readonly label: string;
  readonly icon: ComponentType<{ size?: number; 'aria-hidden'?: boolean | 'true' | 'false' }>;
  readonly order: number;
  readonly group?: string;
  readonly hidden?: boolean;
  readonly home?: boolean;
  readonly tabs?: readonly string[];
  readonly defaultTab?: string;
}
export interface ViewExports {
  readonly View: ComponentType<{ children?: ReactNode }>;
}
export interface UIContribution {
  readonly id: string;
  readonly kind: 'workspace' | 'plugin';
  readonly version: '1.0.0';
  readonly owner?: string;
  readonly slot?: string;
  readonly contractVersion?: '1.0.0';
  readonly slots?: readonly string[];
  readonly navigation?: NavigationContribution;
  readonly wrapsWorkspace?: boolean;
  readonly requires?: readonly string[];
  readonly loadPorts?: () => Promise<Readonly<Record<string, unknown>>>;
  readonly load?: () => Promise<ViewExports>;
}
interface Declaration { readonly contribution: UIContribution }

export function validateContributions(values: readonly UIContribution[]): readonly UIContribution[] {
  const counts = new Map<string, number>();
  for (const item of values) counts.set(item.id, (counts.get(item.id) ?? 0) + 1);
  const unique = values.filter(item => counts.get(item.id) === 1 && item.version === '1.0.0');
  const routes = new Map<string, number>();
  for (const item of unique.filter(item => item.kind === 'workspace')) {
    for (const route of item.navigation ? [item.navigation.path, ...(item.navigation.aliases ?? [])] : []) routes.set(route, (routes.get(route) ?? 0) + 1);
  }
  const acceptedOwners = unique.filter(item => item.kind === 'workspace' && !item.owner && !item.slot &&
    (!item.navigation || [item.navigation.path, ...(item.navigation.aliases ?? [])].every(route => route.startsWith('/') && routes.get(route) === 1)));
  const owners = new Map(acceptedOwners.map(item => [item.id, item]));
  return Object.freeze(unique.filter(item => owners.has(item.id) ||
    (item.kind === 'plugin' &&
    (item.owner && item.slot && item.contractVersion === '1.0.0' && owners.get(item.owner)?.slots?.includes(item.slot)))));
}

const declarations = import.meta.glob<Declaration>([
  '../workspace/**/contribution.tsx', '../plugins/**/contribution.tsx',
], { eager: true });
export const contributions = validateContributions(Object.values(declarations).map(entry => entry.contribution));
export const workspaceContributions = contributions.filter(item => item.kind === 'workspace');
export const navigation = workspaceContributions.flatMap(item => item.navigation ? [item.navigation] : []).sort((a,b) => a.order-b.order);
