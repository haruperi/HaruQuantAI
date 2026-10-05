/** Owner-scoped presentation composition, with missing contributions explicit. */
import { Component, Suspense, lazy, createContext, useContext, type ErrorInfo, type ReactNode } from 'react';
import { contributions, type UIContribution } from './contributions';

class ContributionBoundary extends Component<{ children: ReactNode; fallback?: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError(): { failed: boolean } { return { failed: true }; }
  componentDidCatch(_error: Error, _info: ErrorInfo): void { /* Error text may contain sensitive data; render safe status. */ }
  render(): ReactNode { return this.state.failed ? <><p role="alert">This contribution is unavailable. Stored data is retained.</p>{this.props.fallback}</> : this.props.children; }
}

const views = new Map(contributions.filter(item => item.load).map(item => [item.id, lazy(async () => ({ default: (await item.load!()).View }))]));

interface AttachmentBindings {
  single: ReadonlyMap<string, unknown>;
  multi: ReadonlyMap<string, readonly unknown[]>;
}

const defaultBindings: AttachmentBindings = {
  single: new Map(),
  multi: new Map(),
};

const AttachmentContext = createContext<AttachmentBindings>(defaultBindings);

/** Only handles explicitly bound to this owner are visible in this context. */
export function useAttachment<T>(slot: string): T {
  const ctx = useContext(AttachmentContext);
  const multi = ctx.multi.get(slot);
  if (multi && multi.length > 1) {
    throw new Error(`Ambiguous presentation slot: ${slot}`);
  }
  const value = ctx.single.get(slot);
  if (!value) throw new Error('Missing declared presentation capability');
  return value as T;
}

export function useOptionalAttachment<T>(slot: string): T | undefined {
  const ctx = useContext(AttachmentContext);
  const multi = ctx.multi.get(slot);
  if (multi && multi.length > 1) {
    throw new Error(`Ambiguous presentation slot: ${slot}`);
  }
  return ctx.single.get(slot) as T | undefined;
}

export function useAttachments<T>(slot: string): readonly T[] {
  const ctx = useContext(AttachmentContext);
  return (ctx.multi.get(slot) ?? []) as readonly T[];
}

const composedViews = new Map(workspaceEntries());
function workspaceEntries() {
  return contributions.filter(item => item.kind === 'workspace').map(owner => [owner.id, lazy(async () => {
    const singleBindings = new Map<string, unknown>();
    const multiBindings = new Map<string, unknown[]>();
    for (const child of contributions.filter(item => item.owner === owner.id && item.loadPorts)) {
      if (!child.slot) throw new Error('Missing presentation slot');
      const loaded = Object.freeze({ ...await child.loadPorts!() });
      const currentList = multiBindings.get(child.slot) ?? [];
      currentList.push(loaded);
      multiBindings.set(child.slot, currentList);
      if (!singleBindings.has(child.slot)) {
        singleBindings.set(child.slot, loaded);
      }
    }
    const missing = (owner.requires ?? []).filter(slot => !singleBindings.has(slot));
    const View = views.get(owner.id);
    return { default: () => missing.length || !View
      ? <p role="status">Missing presentation capability: {missing.join(', ') || owner.id}. Stored data is retained.</p>
      : <AttachmentContext.Provider value={{ single: singleBindings, multi: multiBindings }}><View/></AttachmentContext.Provider> };
  })] as const);
}

export function WorkspaceView({ contribution }: { contribution: UIContribution }) {
  const View = composedViews.get(contribution.id);
  if (!View) return <p role="status">Missing presentation capability.</p>;
  let content: ReactNode = <div className="module-area"><View/></div>;
  for (const child of contributions.filter(item => item.owner === contribution.id && item.wrapsWorkspace)) {
    const Wrapper = views.get(child.id);
    if (Wrapper) content = <ContributionBoundary key={child.id} fallback={content}><Wrapper>{content}</Wrapper></ContributionBoundary>;
  }
  return <ContributionBoundary key={contribution.id}><Suspense fallback={<p role="status">Loading workspace…</p>}>{content}</Suspense></ContributionBoundary>;
}

export function EmptyWorkspace() {
  return <div className="module-area"><p role="status">No workspace is installed. The host is ready.</p></div>;
}
