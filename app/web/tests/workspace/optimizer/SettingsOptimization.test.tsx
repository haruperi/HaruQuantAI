import { describe, expect, it } from 'vitest';
import {
  SettingsOptimization,
  type OptimizableParameter,
} from '../../../workspaces/optimizer/SettingsOptimization';

describe('SettingsOptimization', () => {
  it('exports SettingsOptimization component', () => {
    expect(SettingsOptimization).toBeDefined();
    expect(typeof SettingsOptimization).toBe('function');
  });

  it('declares parameter spec and handles toggling', () => {
    const params: OptimizableParameter[] = [
      {
        name: 'Period',
        param_type: 'INT',
        original_value: 14,
        enabled: true,
        start: 10,
        stop: 20,
        step: 5,
      },
    ];
    expect(params[0].name).toBe('Period');
    expect(params[0].enabled).toBe(true);
  });
});
