'use client';

import React, { useMemo, useState } from 'react';
import { Newspaper, ExternalLink } from 'lucide-react';
import {
  NEWS_CATEGORIES,
  NEWS_LANGUAGES,
  type NewsWidgetProps,
} from './contracts';
import styles from './news.module.css';

export const NewsWidget: React.FC<NewsWidgetProps> = ({
  className = '',
  defaultCategories = NEWS_CATEGORIES,
  defaultLanguage = 'en',
  height,
}) => {
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Generate isolated HTML srcDoc to safely run Dukascopy Applet without virtual DOM conflict
  const srcDoc = useMemo(() => {
    const appletConfig = {
      type: 'online_news',
      params: {
        header: false,
        borders: false,
        defaultLanguage,
        availableLanguages: NEWS_LANGUAGES,
        newsCategories: defaultCategories,
        width: '100%',
        height: '100%',
        adv: 'popup',
      },
    };
    const serializedConfig = JSON.stringify(appletConfig);

    return `<!DOCTYPE html>
<html lang="${defaultLanguage}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    html, body {
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background-color: #0b0f19;
      color: #e2e8f0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      overflow-x: hidden;
    }
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: #0b0f19;
    }
    ::-webkit-scrollbar-thumb {
      background: #1e293b;
      border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: #334155;
    }
    iframe {
      width: 100% !important;
      height: 100% !important;
      min-height: 100% !important;
      border: 0 !important;
    }
  </style>
</head>
<body>
  <script type="text/javascript">
    window.DukascopyApplet = ${serializedConfig};
  </script>
  <script type="text/javascript" src="https://freeserv-static.dukascopy.com/2.0/core.js"></script>
</body>
</html>`;
  }, [defaultLanguage, defaultCategories]);

  return (
    <div
      className={`${styles.container} ${className}`}
      style={height ? { height: typeof height === 'number' ? `${height}px` : height } : undefined}
      data-testid="news-widget"
    >
      {/* Clean Top Header */}
      <div className={styles.toolbar}>
        <div className={styles.titleArea}>
          <Newspaper size={16} className={styles.titleIcon} />
          <span>Online News</span>
          <span className={styles.liveBadge} title="Real-time web feed connected">
            <span className={styles.liveDot} />
            Live
          </span>
        </div>
      </div>

      {/* Embedded Iframe Container */}
      <div className={styles.iframeWrapper}>
        {isLoading && (
          <div className={styles.loadingOverlay} data-testid="news-loading">
            <div className={styles.spinner} />
            <span>Loading live news feed...</span>
          </div>
        )}
        <iframe
          title="Dukascopy Online News Feed"
          className={styles.iframe}
          srcDoc={srcDoc}
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
          onLoad={() => setIsLoading(false)}
          data-testid="news-iframe"
        />
      </div>

      {/* Subtle Footer with Attribution */}
      <div className={styles.footer}>
        <span>Provider: Dukascopy Online News Feed</span>
        <a
          href="https://www.dukascopy.com/trading-tools/widgets/news/online_news"
          target="_blank"
          rel="noopener noreferrer"
          className={styles.footerLink}
        >
          Source <ExternalLink size={10} style={{ display: 'inline', verticalAlign: 'middle' }} />
        </a>
      </div>
    </div>
  );
};
