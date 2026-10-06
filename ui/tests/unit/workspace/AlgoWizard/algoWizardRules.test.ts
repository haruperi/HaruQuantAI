import { describe, expect, it } from 'vitest';
import { STRATEGY_TEMPLATES } from '../../../../app/workspace/AlgoWizard/algoWizardTemplates';
import {
  generateEasyLanguageCode,
  generateMql5Code,
  generatePythonCode,
} from '../../../../app/workspace/AlgoWizard/StrategyCodeExportModal';

describe('AlgoWizard Strategy Templates & Rules', () => {
  it('contains 5 pre-seeded StrategyQuant X strategy templates with complete rule trees', () => {
    expect(STRATEGY_TEMPLATES.length).toBe(5);

    const names = STRATEGY_TEMPLATES.map(t => t.name);
    expect(names).toContain('EMA Cross');
    expect(names).toContain('Inside Bar Breakout');
    expect(names).toContain('Range Breakout');
    expect(names).toContain('Mean Reversion');
    expect(names).toContain('Trail Stop by EA');

    STRATEGY_TEMPLATES.forEach(tpl => {
      expect(tpl.rules.length).toBeGreaterThan(0);
      expect(tpl.variables.length).toBeGreaterThan(0);
      expect(tpl.symbol).toBeTruthy();
      expect(tpl.timeframe).toBeTruthy();

      // Check structure of rule nodes
      const hasConditions = tpl.rules.some(r => r.kind === 'condition');
      const hasActions = tpl.rules.some(r => r.kind === 'action');
      expect(hasConditions).toBe(true);
      expect(hasActions).toBe(true);
    });
  });

  it('validates rule-tree node hierarchy and comparison expressions', () => {
    const emaTpl = STRATEGY_TEMPLATES.find(t => t.name === 'EMA Cross')!;
    const conditions = emaTpl.rules.filter(r => r.kind === 'condition');

    expect(conditions.length).toBe(2);
    expect(conditions[0].compOp).toBe('crosses above');
    expect(conditions[0].leftExpr).toBe('EMA(FastPeriod)');
    expect(conditions[0].rightExpr).toBe('EMA(SlowPeriod)');

    expect(conditions[1].compOp).toBe('crosses below');

    const actions = emaTpl.rules.filter(r => r.kind === 'action');
    expect(actions.length).toBe(6);
    expect(actions[0].actionType).toBe('Enter at Market');
    expect(actions[1].actionType).toBe('Set Stop Loss');
    expect(actions[2].actionType).toBe('Set Profit Target');
  });
});

describe('AlgoWizard Multi-Language Code Generation', () => {
  const emaTpl = STRATEGY_TEMPLATES.find(t => t.name === 'EMA Cross')!;

  it('synthesizes working MetaTrader 5 (MQL5) Expert Advisor code', () => {
    const mqlCode = generateMql5Code(
      emaTpl.rules,
      emaTpl.variables,
      emaTpl.name,
      emaTpl.symbol,
      emaTpl.timeframe
    );

    expect(mqlCode).toContain('#property strict');
    expect(mqlCode).toContain('#include <Trade\\Trade.mqh>');
    expect(mqlCode).toContain('input double FastPeriod = 20;');
    expect(mqlCode).toContain('input double SlowPeriod = 50;');
    expect(mqlCode).toContain('int OnInit()');
    expect(mqlCode).toContain('void OnTick()');
    expect(mqlCode).toContain('trade.PositionOpen');
  });

  it('synthesizes working EasyLanguage / TradeStation strategy code', () => {
    const elCode = generateEasyLanguageCode(emaTpl.rules, emaTpl.variables, emaTpl.name);

    expect(elCode).toContain('Inputs:');
    expect(elCode).toContain('FastPeriod(20)');
    expect(elCode).toContain('SlowPeriod(50)');
    expect(elCode).toContain('Variables:');
    expect(elCode).toContain('Buy ("LE") next bar at market;');
    expect(elCode).toContain('SetStopLoss(StopLoss);');
    expect(elCode).toContain('SetProfitTarget(TakeProfit);');
  });

  it('synthesizes clean Python / Pandas vectorized strategy code', () => {
    const pyCode = generatePythonCode(
      emaTpl.rules,
      emaTpl.variables,
      emaTpl.name,
      emaTpl.symbol,
      emaTpl.timeframe
    );

    expect(pyCode).toContain('import pandas as pd');
    expect(pyCode).toContain('import numpy as np');
    expect(pyCode).toContain('class EMACrossStrategy:');
    expect(pyCode).toContain('FastPeriod = 20');
    expect(pyCode).toContain('SlowPeriod = 50');
    expect(pyCode).toContain('def generate_signals(self) -> pd.DataFrame:');
    expect(pyCode).toContain("df['signal'] = 0");
    expect(pyCode).toContain("df['strategy_returns']");
  });
});
