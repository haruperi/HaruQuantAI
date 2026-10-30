export type DashboardPanelDescriptor = {
  name: string;
  product?: string | null;
};

export function selectDashboardPanels<T extends DashboardPanelDescriptor>(
  panels: readonly T[],
  product: string,
): T[] {
  return panels.filter((panel) => !panel.product || panel.product === product);
}
