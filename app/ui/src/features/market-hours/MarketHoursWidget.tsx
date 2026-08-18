'use client';

import React, { useMemo, useState } from 'react';
import { Clock } from 'lucide-react';
import {
  DEFAULT_MARKET_HOURS_CONFIG,
  MarketHoursWidgetConfig,
  MarketHoursWidgetProps,
} from './contracts';
import styles from './market-hours.module.css';

/**
 * Builds the isolated HTML payload for the sandboxed Dukascopy FX Market Hours iframe.
 *
 * @param config Complete MarketHoursWidgetConfig object
 * @returns Fully formatted HTML document string with dark theme overrides
 */
function buildMarketHoursSrcDoc(config: MarketHoursWidgetConfig): string {
  const appletJson = JSON.stringify({
    type: 'fxmarkethours',
    params: {
      showHeader: config.showHeader,
      displayMainMenu: config.displayMainMenu,
      displayTimezoneChange: config.displayTimezoneChange,
      displayInstrumentChange: config.displayInstrumentChange,
      displaySpreadIndicator: config.displaySpreadIndicator,
      displayVolumeIndicator: config.displayVolumeIndicator,
      displayVolatilityIndicator: config.displayVolatilityIndicator,
      displayFollowButton: config.displayFollowButton,
      allowTimezoneChange: config.allowTimezoneChange,
      allowInstrumentChange: config.allowInstrumentChange,
      defaultTimezone: config.defaultTimezone,
      showIndicator: config.showIndicator,
      defaultFollowMode: config.defaultFollowMode,
      worldMapColor: config.worldMapColor,
      hoursBackground: config.hoursBackground,
      hoursActiveBackground: config.hoursActiveBackground,
      hoursTextColor: config.hoursTextColor,
      currentHourBGColor: config.currentHourBGColor,
      dstHourColor: config.dstHourColor,
      indicatorBarColor: config.indicatorBarColor,
      graphPointsColor: config.graphPointsColor,
      spreadTopGraphColor: config.spreadTopGraphColor,
      spreadBottomGraphColor: config.spreadBottomGraphColor,
      volatilityGraphColor: config.volatilityGraphColor,
      instrument: config.instrument,
      width: config.width,
      height: config.height,
      adv: config.adv,
    },
  });

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    html, body {
      width: 100%;
      height: 100%;
      background-color: #0b0f19;
      color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      overflow-x: hidden;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }
    #dukascopy-widget-container {
      width: 100%;
      height: 100%;
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    #dukascopy-widget-container > iframe,
    iframe {
      width: 100% !important;
      height: 100% !important;
      min-height: 100% !important;
      border: 0 !important;
      flex: 1 !important;
    }
    /* Custom scrollbar matching HaruQuantAI theme */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: #0b0f19;
    }
    ::-webkit-scrollbar-thumb {
      background: #334155;
      border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: #475569;
    }
  </style>
</head>
<body>
  <div id="dukascopy-widget-container">
    <script type="text/javascript">
      window.DukascopyApplet = ${appletJson};
    </script>
    <script type="text/javascript" src="https://freeserv-static.dukascopy.com/2.0/core.js"></script>
  </div>
</body>
</html>`;
}

/**
 * FEAT-UI-30 FX Market Hours Widget.
 *
 * Embeds Dukascopy's real-time FX Market Hours trading clock and session statistics
 * inside an isolated iframe, eliminating virtual DOM disruptions while supporting
 * dark theme configuration, timezone management, and interactive session indicators.
 */
export const MarketHoursWidget: React.FC<MarketHoursWidgetProps> = ({
  config: configProp,
  height = '100%',
  className,
  title = 'FX Market Hours',
}) => {
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const mergedConfig: MarketHoursWidgetConfig = useMemo(() => {
    return {
      ...DEFAULT_MARKET_HOURS_CONFIG,
      ...(configProp || {}),
    };
  }, [configProp]);

  const srcDocContent = useMemo(() => {
    return buildMarketHoursSrcDoc(mergedConfig);
  }, [mergedConfig]);

  const handleIframeLoad = () => {
    setIsLoading(false);
  };

  const containerStyle: React.CSSProperties = {
    height: typeof height === 'number' ? `${height}px` : height,
  };

  return (
    <div
      className={`${styles.container} ${className || ''}`}
      style={containerStyle}
      data-testid="market-hours-widget"
    >
      {/* Clean Host Header */}
      <div className={styles.toolbar}>
        <div className={styles.titleArea}>
          <Clock className={styles.titleIcon} aria-hidden="true" />
          <span>{title}</span>
        </div>

        <div className={styles.liveBadge} data-testid="market-hours-live-badge">
          <span className={styles.liveDot} />
          <span>LIVE SESSIONS</span>
        </div>
      </div>

      {/* Sandboxed Iframe Container */}
      <div className={styles.iframeWrapper}>
        {isLoading && (
          <div className={styles.loadingOverlay} data-testid="market-hours-loading">
            <div className={styles.spinner} />
            <span>Connecting to Market Hours feed...</span>
          </div>
        )}

        <iframe
          title="FX Market Hours Feed"
          srcDoc={srcDocContent}
          className={styles.iframe}
          onLoad={handleIframeLoad}
          data-testid="market-hours-iframe"
        />
      </div>

      {/* Attribution Footer */}
      <div className={styles.footer}>
        <span>Asian • European • North American Trading Sessions</span>
        <span>
          Data provided by{' '}
          <a
            href="https://www.dukascopy.com"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.footerLink}
          >
            Dukascopy Swiss FX
          </a>
        </span>
      </div>
    </div>
  );
};
