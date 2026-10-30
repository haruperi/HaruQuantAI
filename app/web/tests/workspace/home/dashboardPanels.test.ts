import { test, expect } from 'vitest';
import {
  selectDashboardPanels,
  type DashboardPanelDescriptor,
} from '../../../workspaces/home/dashboardPanels';

test('filters products', () => {
  const panels: readonly DashboardPanelDescriptor[] = [
    { name: 'shared' },
    { name: 'empty', product: '' },
    { name: 'builder', product: 'BUILDER' },
    { name: 'other', product: 'RETESTER' },
    { name: 'null', product: null },
  ];
  const selected = selectDashboardPanels(panels, 'BUILDER');
  expect(selected.map((p) => p.name)).toEqual([
    'shared',
    'empty',
    'builder',
    'null',
  ]);
});

test('uses exact product matching', () => {
  const panels: readonly DashboardPanelDescriptor[] = [
    { name: 'builder', product: 'BUILDER' },
  ];
  const selected = selectDashboardPanels(panels, 'builder');
  expect(selected).toEqual([]);
});

test('handles empty input', () => {
  const empty: readonly DashboardPanelDescriptor[] = [];
  const selected = selectDashboardPanels(empty, 'BUILDER');
  expect(selected).toEqual([]);
  expect(selected).not.toBe(empty);
});

test('retains references and duplicates without mutation', () => {
  type CustomPanel = DashboardPanelDescriptor & { extra?: number };
  const panel1: CustomPanel = Object.freeze({
    name: 'item',
    product: 'BUILDER',
    extra: 123,
  });
  const panel2: CustomPanel = Object.freeze({
    name: 'other',
    product: 'RETESTER',
  });
  const input: readonly CustomPanel[] = Object.freeze([panel1, panel2, panel1]);

  const result = selectDashboardPanels(input, 'BUILDER');

  expect(result.length).toBe(2);
  expect(result[0]).toBe(panel1);
  expect(result[1]).toBe(panel1);
  expect(result[0].extra).toBe(123);
  expect(input.length).toBe(3);
});
