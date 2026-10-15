import { useCallback, useEffect, useState } from 'react';
import {
  Clock,
  Database,
  Download,
  FileSpreadsheet,
  HardDrive,
  Layers,
  Radio,
  RefreshCw,
} from 'lucide-react';
import { createDomainClient } from '../../host/transport';

const dataClient = createDomainClient('/data');

export interface DataHomeSummary {
  workspace_name?: string;
  datasets_count: number;
  instruments_count: number;
  sessions_count: number;
  baskets_count: number;
  active_providers_count: number;
  total_bars: number;
  storage_bytes?: number;
  parquet_files_count?: number;
}

export interface DataHomeDashboard {
  symbol: string;
  instrument: string;
  broker_profile: string;
  underlying_symbol: string;
  timeframe: string;
  timezone: string;
  date_from: string;
  date_to: string;
  total_days: number;
  total_records: number;
  source: string;
  data_type: string;
}

interface DataManagerHomeProps {
  onNavigateTab?: (tabName: string) => void;
  onOpenImport?: () => void;
  onOpenDownload?: () => void;
}

export function DataManagerHome({ onNavigateTab, onOpenImport, onOpenDownload }: DataManagerHomeProps) {
  const [overview, setOverview] = useState<DataHomeSummary>({
    datasets_count: 0,
    instruments_count: 0,
    sessions_count: 0,
    baskets_count: 0,
    active_providers_count: 0,
    total_bars: 0,
  });
  const [datasets, setDatasets] = useState<DataHomeDashboard[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    try {
      const data = await dataClient.get<DataHomeSummary>('/home/overview');
      if (data) {
        setOverview(data);
      }
    } catch {
      // Keep existing overview on error
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDatasets = useCallback(async () => {
    try {
      const items = await dataClient.get<DataHomeDashboard[]>('/home/datasets');
      if (Array.isArray(items)) {
        setDatasets(items);
      }
    } catch {
      // Keep existing datasets on error
    }
  }, []);

  useEffect(() => {
    fetchOverview();
    fetchDatasets();
  }, [fetchOverview, fetchDatasets]);

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
            onClick={() => {
              fetchOverview();
              fetchDatasets();
            }}
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
              <span>Import CSV, TXT, or history files</span>
            </div>
          </button>
          <button
            className="dm-action-card"
            onClick={() => onOpenDownload ? onOpenDownload() : onNavigateTab?.('Data sources')}
          >
            <Radio size={18} />
            <div className="dm-action-text">
              <strong>Download Online Data</strong>
              <span>Fetch tick & M1 bars from data providers</span>
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

      {/* Saved Datasets Catalog Table */}
      <section className="dm-datasets-section" aria-label="Saved Datasets Catalog">
        <div className="dm-datasets-header">
          <h2 className="dm-section-title">Saved Datasets Catalog ({datasets.length})</h2>
          <span className="dm-datasets-caption">Live data partitioned from SQLite datamgr_datasets</span>
        </div>
        <div className="dm-datasets-table-wrap">
          <table className="dm-datasets-table" aria-label="Saved datasets table">
            <thead>
              <tr>
                <th>Symbol Name</th>
                <th>Instrument</th>
                <th>Broker profile</th>
                <th>Underlying Symbol</th>
                <th>Timeframe</th>
                <th>Timezone</th>
                <th>Date from</th>
                <th>Date to</th>
                <th style={{ textAlign: 'right' }}>Total Days</th>
                <th style={{ textAlign: 'right' }}>Total Records</th>
                <th>Source</th>
                <th>Data type</th>
              </tr>
            </thead>
            <tbody>
              {datasets.length === 0 ? (
                <tr>
                  <td colSpan={12} style={{ textAlign: 'center', padding: '24px', color: 'var(--muted)' }}>
                    No saved datasets found in catalog.
                  </td>
                </tr>
              ) : (
                datasets.map((ds, idx) => (
                  <tr key={`${ds.symbol}-${ds.broker_profile}-${ds.timeframe}-${idx}`}>
                    <td className="dm-cell-bold">{ds.symbol}</td>
                    <td>{ds.instrument}</td>
                    <td>{ds.broker_profile}</td>
                    <td>{ds.underlying_symbol}</td>
                    <td><span className="dm-badge-tf">{ds.timeframe}</span></td>
                    <td>{ds.timezone}</td>
                    <td>{ds.date_from || '-'}</td>
                    <td>{ds.date_to || '-'}</td>
                    <td style={{ textAlign: 'right' }}>{ds.total_days.toLocaleString()}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>{ds.total_records.toLocaleString()}</td>
                    <td>{ds.source}</td>
                    <td><span className="dm-badge-type">{ds.data_type}</span></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
