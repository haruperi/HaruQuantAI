/**
 * REST API client for HaruQuantAI Broker Profiles.
 *
 * Communicates with backend endpoints (/data/brokers, /api/v1/data/brokers)
 * to provide full SQX-parity broker profile lifecycle operations:
 * - Profile CRUD (create, read, update, delete)
 * - Stock ticker list inspection and replacement
 * - CSV import and export for stock tickers
 * - StrategyQuant X XML import and export (<Brokers><Broker>...<Stocks>)
 * - MetaTrader 4/5 XML inspection and selective record import
 * - Historical data update trigger for broker profile stocks
 */

import { createDomainClient, type DomainClient } from '../../../../host/transport';
import type { BrokerProfile } from './brokerProfiles';

export interface RemoteBrokerRecord {
  id: number;
  name: string;
  description: string;
  stockpicker_use: boolean;
  mt_use: boolean;
  broker_timezone: string;
  postfix: string;
  is_system: boolean;
  stocks?: string[];
  customized_stocks?: number;
  total_instruments?: number;
  total_sessions?: number;
}

export interface XmlOverviewItem {
  name: string;
  description: string;
  source: string;
}

export interface BrokerDataUpdateResponse {
  broker_id: number;
  broker_name: string;
  status: string;
  message: string;
  stock_count: number;
  stocks: string[];
}

let client: DomainClient = createDomainClient('/data');

export function setBrokerApiClient(customClient: DomainClient): void {
  client = customClient;
}

export function toBrokerProfile(record: RemoteBrokerRecord, stocks?: string[]): BrokerProfile {
  return {
    id: String(record.id),
    name: record.name,
    desc: record.description || '',
    postfix: record.postfix || '',
    timezone: record.broker_timezone || 'UTC',
    mtUse: Boolean(record.mt_use),
    stockPickerUse: Boolean(record.stockpicker_use),
    system: Boolean(record.is_system),
    stocks: stocks ?? (record.stocks ? [...record.stocks] : []),
    instruments: [],
  };
}

export async function fetchBrokers(): Promise<BrokerProfile[]> {
  const records = await client.get<RemoteBrokerRecord[]>('/brokers');
  return records.map(rec => toBrokerProfile(rec));
}

export async function getBroker(id: string | number): Promise<BrokerProfile> {
  const numericId = typeof id === 'number' ? id : parseInt(id, 10);
  const record = await client.get<RemoteBrokerRecord>(`/brokers/${numericId}`);
  return toBrokerProfile(record);
}

export async function saveBroker(profile: BrokerProfile): Promise<BrokerProfile> {
  const isNumeric = /^\d+$/.test(profile.id);
  const payload = {
    id: isNumeric ? parseInt(profile.id, 10) : undefined,
    name: profile.name,
    desc: profile.desc,
    stockpicker_use: profile.stockPickerUse,
    mt_use: profile.mtUse,
    mt_timezone: profile.timezone,
    postfix: profile.postfix,
  };
  const record = await client.post<RemoteBrokerRecord>('/brokers', payload);
  return toBrokerProfile(record, profile.stocks);
}

export async function deleteBrokers(ids: Array<string | number>): Promise<number> {
  const numericIds = ids
    .map(id => (typeof id === 'number' ? id : parseInt(id, 10)))
    .filter(id => !Number.isNaN(id));

  const resp = await client.post<{ deleted_count: number }>('/brokers/delete', {
    broker_ids: numericIds,
  });
  return resp.deleted_count;
}

export async function fetchBrokerStocks(brokerId: string | number): Promise<string[]> {
  const numericId = typeof brokerId === 'number' ? brokerId : parseInt(brokerId, 10);
  const resp = await client.get<{ broker_id: number; stocks: string[] }>(`/brokers/${numericId}/stocks`);
  return resp.stocks ?? [];
}

export async function saveBrokerStocks(brokerId: string | number, stocks: string[]): Promise<number> {
  const numericId = typeof brokerId === 'number' ? brokerId : parseInt(brokerId, 10);
  const resp = await client.put<{ broker_id: number; count: number }>(`/brokers/${numericId}/stocks`, {
    stocks,
  });
  return resp.count;
}

export async function importBrokerStocks(brokerId: string | number, csvContent: string): Promise<number> {
  const numericId = typeof brokerId === 'number' ? brokerId : parseInt(brokerId, 10);
  const resp = await client.post<{ broker_id: number; count: number }>(`/brokers/${numericId}/stocks/import`, {
    content: csvContent,
  });
  return resp.count;
}

export async function exportBrokerStocks(brokerId: string | number): Promise<string> {
  const numericId = typeof brokerId === 'number' ? brokerId : parseInt(brokerId, 10);
  const resp = await client.get<{ broker_id: number; content: string }>(`/brokers/${numericId}/stocks/export`);
  return resp.content;
}

export async function exportBrokersXml(brokerIds: Array<string | number>): Promise<string> {
  const numericIds = brokerIds
    .map(id => (typeof id === 'number' ? id : parseInt(id, 10)))
    .filter(id => !Number.isNaN(id));

  const resp = await client.post<{ xml_content: string }>('/brokers/save-xml', {
    broker_ids: numericIds,
  });
  return resp.xml_content;
}

export async function importBrokersXml(xmlContent: string): Promise<BrokerProfile[]> {
  const records = await client.post<RemoteBrokerRecord[]>('/brokers/load-xml', {
    xml_content: xmlContent,
  });
  return records.map(rec => toBrokerProfile(rec));
}

export async function inspectXmlOverview(
  xmlContent: string,
  kind: 'instrument' | 'session'
): Promise<XmlOverviewItem[]> {
  return client.post<XmlOverviewItem[]>('/brokers/import-get-overview', {
    xml_content: xmlContent,
    kind,
  });
}

export async function importXmlRecords(
  xmlContent: string,
  kind: 'instrument' | 'session',
  brokerId: string | number,
  postfix: string,
  selectedNames: string[]
): Promise<number> {
  const numericId = typeof brokerId === 'number' ? brokerId : parseInt(brokerId, 10);
  const resp = await client.post<{ imported_count: number }>('/brokers/import-session-instrument', {
    xml_content: xmlContent,
    kind,
    broker_id: numericId,
    postfix,
    selected_names: selectedNames,
  });
  return resp.imported_count;
}

export async function triggerBrokerDataUpdate(brokerId: string | number): Promise<BrokerDataUpdateResponse> {
  const numericId = typeof brokerId === 'number' ? brokerId : parseInt(brokerId, 10);
  return client.post<BrokerDataUpdateResponse>(`/brokers/${numericId}/update-data`, {});
}
