import { SMA } from './SMA';
import { EMA } from './EMA';
import { WMA } from './WMA';
import { BollingerBands } from './BollingerBands';
import { VWAP } from './VWAP';
import { RSI } from './RSI';
import { MACD } from './MACD';
import { Stochastic } from './Stochastic';
import { Volume } from './Volume';
import { ATR } from './ATR';
import type { IndicatorId } from '../types';
import type { IndicatorDefinition } from './types';
export const indicators: Record<IndicatorId, IndicatorDefinition> = {
  SMA,
  EMA,
  WMA,
  BollingerBands,
  VWAP,
  RSI,
  MACD,
  Stochastic,
  Volume,
  ATR,
};
