import { useCallback, useEffect, useState } from 'react';
import {
  BookOpen, ChevronDown, ChevronUp, Database, Download, ExternalLink,
  FileSpreadsheet, HardDrive, Layers, Radio, RefreshCw, Terminal, Clock,
} from 'lucide-react';
import { createDomainClient } from '../../host/transport';

const dataClient = createDomainClient('/data');

export interface HomeOverviewData {
  workspace_name?: string;
  datasets_count: number;
  instruments_count: number;
  sessions_count: number;
  baskets_count: number;
  active_providers_count: number;
  total_bars: number;
}

export interface DocLinkItem {
  id: string;
  title: string;
  description: string;
  icon?: string;
  url: string;
}

interface DataManagerHomeProps {
  onNavigateTab?: (tabName: string) => void;
  onOpenImport?: () => void;
  onOpenDownload?: () => void;
}

const defaultDocLinks: DocLinkItem[] = [
  {
    id: 'import-mt4',
    title: 'Import History Data MT4',
    description: 'Learn how to import historical data to MetaTrader 4',
    url: 'https://strategyquant.com/doc/quantdatamanager/import-history-data-metatrader-4/',
  },
  {
    id: 'test-mt4',
    title: 'Test Strategy MT4',
    description: 'Test your strategy in MT4 with tick precision',
    url: 'https://strategyquant.com/doc/quantdatamanager/test-strategy-metatrader-4-tick-precision/',
  },
  {
    id: 'import-mt5',
    title: 'Import Data to MT5',
    description: 'How to import data to MetaTrader 5',
    url: 'https://strategyquant.com/doc/quantdatamanager/how-to-import-data-to-metatrader-5/',
  },
  {
    id: 'export-mt5',
    title: 'Export Data from MT5',
    description: 'How to export data from MetaTrader 5',
    url: 'https://strategyquant.com/doc/quantdatamanager/how-to-export-data-from-metatrader-5/',
  },
  {
    id: 'cli-intro',
    title: 'Introduction to CLI',
    description: 'What is CLI and how to use it for data automation',
    url: 'https://strategyquant.com/doc/cli-command-line/introduction-to-cli/',
  },
  {
    id: 'full-doc',
    title: 'Full Documentation',
    description: 'Browse complete Data Manager documentation and guides',
    url: 'https://strategyquant.com/doc/quantdatamanager/',
  },
];

const faqs = [
  {
    q: 'Is the data provided for free? What is the data source?',
    a: 'High quality tick data for forex and CFDs are provided for free by Dukascopy and multiple connected online providers. HaruQuantAI downloads, decompresses, normalizes, and stores this data into high-performance partitioned Parquet format on your local machine.',
  },
  {
    q: 'What does Verified downloads mean?',
    a: 'Verified downloads ensure that the data downloaded is bit-for-bit validated against checksums and server headers from the source provider (e.g. Dukascopy, Darwinex, Yahoo). Corrupt or partial downloads are automatically discarded and retried.',
  },
  {
    q: 'Can HaruQuantAI download data for stocks, commodities, crypto?',
    a: 'Yes. HaruQuantAI supports multiple data providers including Dukascopy, Yahoo Finance (stocks & ETFs), Binance/Coinbase (crypto), Darwinex, and custom local file formats (CSV, NinjaTrader, MetaTrader).',
  },
  {
    q: 'How can I transfer tick data to MetaTrader?',
    a: 'HaruQuantAI allows direct export to MetaTrader 4 FXT & HST files with tick precision modeling quality, as well as MetaTrader 5 custom symbol CSV formats via the Export tab.',
  },
];

export function DataManagerHome({ onNavigateTab, onOpenImport, onOpenDownload }: DataManagerHomeProps) {
  const [overview, setOverview] = useState<HomeOverviewData>({
    datasets_count: 0,
    instruments_count: 0,
    sessions_count: 0,
    baskets_count: 0,
    active_providers_count: 0,
    total_bars: 0,
  });
  const [docLinks, setDocLinks] = useState<DocLinkItem[]>(defaultDocLinks);
  const [loading, setLoading] = useState(false);
  const [activeFaq, setActiveFaq] = useState<number | null>(null);

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    try {
      const data = await dataClient.get<HomeOverviewData>('/home/overview');
      if (data) {
        setOverview(data);
      }
    } catch {
      // Keep existing overview on error
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDocLinks = useCallback(async () => {
    try {
      const links = await dataClient.get<DocLinkItem[]>('/home/doc-links');
      if (Array.isArray(links) && links.length > 0) {
        setDocLinks(links);
      }
    } catch {
      // Fall back to default links
    }
  }, []);

  useEffect(() => {
    fetchOverview();
    fetchDocLinks();
  }, [fetchOverview, fetchDocLinks]);

  return (
    <div className="dm-home-container" role="region" aria-label="Data Manager Home">
      {/* Hero Header */}
      <header className="dm-home-header">
        <div className="dm-home-title-group">
          <span className="dm-home-kicker">HaruQuantAI Market Data Engine</span>
          <h1 className="dm-home-heading">Data Manager Home</h1>
          <p className="dm-home-subheading">
            Authoritative partitioned Parquet historical storage, data catalog, and multi-provider pipelines.
          </p>
        </div>
        <div className="dm-home-status-card">
          <div className="dm-status-item">
            <span className="dm-status-label">Storage Engine</span>
            <span className="dm-status-val">Partitioned Parquet (ZSTD lvl 6)</span>
          </div>
          <div className="dm-status-item">
            <span className="dm-status-label">Catalog Database</span>
            <span className="dm-status-val">SQLite (datamgr_datasets)</span>
          </div>
          <button
            className="dm-refresh-btn"
            onClick={fetchOverview}
            disabled={loading}
            aria-label="Refresh overview"
          >
            <RefreshCw size={13} className={loading ? 'spinning' : ''} />
            <span>{loading ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </header>

      {/* Metrics Grid */}
      <section className="dm-metrics-section" aria-label="Catalog Overview Metrics">
        <div className="dm-metric-card">
          <div className="dm-metric-icon-wrap" style={{ background: '#1e3a5f', color: '#60a5fa' }}>
            <Database size={22} />
          </div>
          <div className="dm-metric-info">
            <span className="dm-metric-num" data-testid="metric-datasets-count">
              {overview.datasets_count.toLocaleString()}
            </span>
            <span className="dm-metric-label">Total Datasets</span>
          </div>
        </div>

        <div className="dm-metric-card">
          <div className="dm-metric-icon-wrap" style={{ background: '#1c3d3d', color: '#2dd4bf' }}>
            <Layers size={22} />
          </div>
          <div className="dm-metric-info">
            <span className="dm-metric-num" data-testid="metric-total-bars">
              {overview.total_bars.toLocaleString()}
            </span>
            <span className="dm-metric-label">Historical Bars (M1/Ticks)</span>
          </div>
        </div>

        <div className="dm-metric-card">
          <div className="dm-metric-icon-wrap" style={{ background: '#3b2f1e', color: '#f59e0b' }}>
            <HardDrive size={22} />
          </div>
          <div className="dm-metric-info">
            <span className="dm-metric-num" data-testid="metric-instruments-count">
              {overview.instruments_count.toLocaleString()}
            </span>
            <span className="dm-metric-label">Instruments</span>
          </div>
        </div>

        <div className="dm-metric-card">
          <div className="dm-metric-icon-wrap" style={{ background: '#2c1e3f', color: '#c084fc' }}>
            <Clock size={22} />
          </div>
          <div className="dm-metric-info">
            <span className="dm-metric-num" data-testid="metric-sessions-count">
              {overview.sessions_count.toLocaleString()}
            </span>
            <span className="dm-metric-label">Trading Sessions</span>
          </div>
        </div>

        <div className="dm-metric-card">
          <div className="dm-metric-icon-wrap" style={{ background: '#1f2e3d', color: '#38bdf8' }}>
            <Radio size={22} />
          </div>
          <div className="dm-metric-info">
            <span className="dm-metric-num" data-testid="metric-active-providers">
              {overview.active_providers_count.toLocaleString()}
            </span>
            <span className="dm-metric-label">Active Providers</span>
          </div>
        </div>

        <div className="dm-metric-card">
          <div className="dm-metric-icon-wrap" style={{ background: '#362130', color: '#f43f5e' }}>
            <FileSpreadsheet size={22} />
          </div>
          <div className="dm-metric-info">
            <span className="dm-metric-num" data-testid="metric-baskets-count">
              {overview.baskets_count.toLocaleString()}
            </span>
            <span className="dm-metric-label">Custom Baskets</span>
          </div>
        </div>
      </section>

      {/* Quick Actions Bar */}
      <section className="dm-quick-actions" aria-label="Quick Actions">
        <h2 className="dm-section-title">Quick Actions</h2>
        <div className="dm-actions-grid">
          <button
            className="dm-action-card"
            onClick={() => onOpenImport ? onOpenImport() : onNavigateTab?.('Data sources')}
          >
            <Download size={18} />
            <div className="dm-action-text">
              <strong>Import Market Data</strong>
              <span>Import CSV, TXT, or MetaTrader history files</span>
            </div>
          </button>
          <button
            className="dm-action-card"
            onClick={() => onOpenDownload ? onOpenDownload() : onNavigateTab?.('Data sources')}
          >
            <Radio size={18} />
            <div className="dm-action-text">
              <strong>Download Online Data</strong>
              <span>Fetch tick & M1 bars from Dukascopy, Yahoo, or Crypto</span>
            </div>
          </button>
          <button
            className="dm-action-card"
            onClick={() => onNavigateTab?.('Instruments')}
          >
            <HardDrive size={18} />
            <div className="dm-action-text">
              <strong>Configure Instruments</strong>
              <span>Manage pip sizes, spreads, commissions, and multipliers</span>
            </div>
          </button>
          <button
            className="dm-action-card"
            onClick={() => onNavigateTab?.('Sessions')}
          >
            <Clock size={18} />
            <div className="dm-action-text">
              <strong>Trading Sessions</strong>
              <span>Define RTH / ETH trading hours and rollover windows</span>
            </div>
          </button>
        </div>
      </section>

      {/* Documentation & Guides Grid (mirroring SQX offline/index.html) */}
      <section className="dm-docs-section" aria-label="Documentation and Guides">
        <h2 className="dm-section-title">Documentation & Tutorials</h2>
        <div className="dm-docs-grid">
          {docLinks.map(link => (
            <a
              key={link.id}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="dm-doc-card"
            >
              <div className="dm-doc-icon">
                {link.id.includes('cli') ? (
                  <Terminal size={18} />
                ) : link.id.includes('mt') ? (
                  <FileSpreadsheet size={18} />
                ) : (
                  <BookOpen size={18} />
                )}
              </div>
              <div className="dm-doc-content">
                <div className="dm-doc-header">
                  <h3 className="dm-doc-title">{link.title}</h3>
                  <ExternalLink size={12} className="dm-doc-ext" />
                </div>
                <p className="dm-doc-desc">{link.description}</p>
              </div>
            </a>
          ))}
        </div>
      </section>

      {/* Frequently Asked Questions (mirroring SQX offline/index.html) */}
      <section className="dm-faq-section" aria-label="Frequently Asked Questions">
        <h2 className="dm-section-title">Frequently Asked Questions</h2>
        <div className="dm-faq-list">
          {faqs.map((faq, idx) => {
            const isOpen = activeFaq === idx;
            return (
              <div key={idx} className={`dm-faq-item ${isOpen ? 'active' : ''}`}>
                <button
                  className="dm-faq-question"
                  onClick={() => setActiveFaq(isOpen ? null : idx)}
                  aria-expanded={isOpen}
                >
                  <span className="dm-faq-question-text">{faq.q}</span>
                  {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
                {isOpen && (
                  <div className="dm-faq-answer">
                    <p>{faq.a}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
