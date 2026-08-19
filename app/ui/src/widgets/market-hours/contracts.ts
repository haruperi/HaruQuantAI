/**
 * Contracts and types for FEAT-UI-30 FX Market Hours Widget.
 *
 * Configures the embeddable Dukascopy FX Market Hours applet, supporting
 * interactive Asian, European, and North American session clocks, volatility/spread/volume
 * indicator panels, and CME dark theme parameterization.
 */

export interface MarketHoursWidgetConfig {
  showHeader: boolean;
  displayMainMenu: boolean;
  displayTimezoneChange: boolean;
  displayInstrumentChange: boolean;
  displaySpreadIndicator: boolean;
  displayVolumeIndicator: boolean;
  displayVolatilityIndicator: boolean;
  displayFollowButton: boolean;
  allowTimezoneChange: boolean;
  allowInstrumentChange: boolean;
  defaultTimezone: number;
  showIndicator: string;
  defaultFollowMode: boolean;
  worldMapColor: string;
  hoursBackground: string;
  hoursActiveBackground: string;
  hoursTextColor: string;
  currentHourBGColor: string;
  dstHourColor: string;
  indicatorBarColor: string;
  graphPointsColor: string;
  spreadTopGraphColor: string;
  spreadBottomGraphColor: string;
  volatilityGraphColor: string;
  instrument: string;
  width: string;
  height: string;
  adv: string;
}

export const DEFAULT_MARKET_HOURS_CONFIG: MarketHoursWidgetConfig = {
  showHeader: false,
  displayMainMenu: true,
  displayTimezoneChange: true,
  displayInstrumentChange: true,
  displaySpreadIndicator: true,
  displayVolumeIndicator: true,
  displayVolatilityIndicator: true,
  displayFollowButton: true,
  allowTimezoneChange: true,
  allowInstrumentChange: true,
  defaultTimezone: 0,
  showIndicator: '0',
  defaultFollowMode: false,
  worldMapColor: '#1e293b',
  hoursBackground: '#131b2e',
  hoursActiveBackground: '#0284c7',
  hoursTextColor: '#f8fafc',
  currentHourBGColor: '#38bdf8',
  dstHourColor: '#06b6d4',
  indicatorBarColor: '#0284c7',
  graphPointsColor: '#f8fafc',
  spreadTopGraphColor: '#10b981',
  spreadBottomGraphColor: '#ef4444',
  volatilityGraphColor: '#f59e0b',
  instrument: 'EUR/USD',
  width: '100%',
  height: '100%',
  adv: 'popup',
};

export const POPULAR_FX_INSTRUMENTS = [
  'EUR/USD',
  'GBP/USD',
  'USD/JPY',
  'USD/CHF',
  'AUD/USD',
  'USD/CAD',
  'NZD/USD',
  'EUR/GBP',
  'EUR/JPY',
  'GBP/JPY',
] as const;

export interface MarketHoursWidgetProps {
  /**
   * Optional partial configuration overrides for the Dukascopy FX Market Hours applet.
   */
  config?: Partial<MarketHoursWidgetConfig>;

  /**
   * Height of the widget container (e.g. '100%', '600px').
   * @default '100%'
   */
  height?: string | number;

  /**
   * Optional custom CSS class name for outer wrapper.
   */
  className?: string;

  /**
   * Optional custom title for the widget header.
   * @default 'FX Market Hours'
   */
  title?: string;
}
