/**
 * REST API client for HaruQuantAI Stock Groups (Baskets).
 *
 * Communicates with backend endpoints (/data/baskets, /data/baskets/overview, /data/baskets/update-data,
 * /basketOfStocks/list, etc.) to provide full SQX-parity stock group lifecycle operations:
 * - Group overview inspection (8 SQX table columns)
 * - Group CRUD and stock constituent management
 * - CSV import and export for constituents (Ticker;From;To)
 * - StrategyQuant X XML import and export (<Groups><Group name="...">...)
 * - Automatic data update trigger for group constituents
 * - 100% data readiness evaluation
 */

import { createDomainClient, type DomainClient } from '../../../../host/transport';
import type { StockGroupDefinition } from './stockGroups';

export interface RemoteBasketItem {
  symbol: string;
  weight?: number;
  date_from?: string | null;
  date_to?: string | null;
}

export interface RemoteBasketRecord {
  id?: number;
  name: string;
  description: string;
  system: boolean;
  items: RemoteBasketItem[];
}

export interface StockGroupOverviewItem {
  id: number;
  name: string;
  description: string;
  system: boolean;
  active_count: number;
  total_count: number;
  symbols_count: number;
  downloaded_count: number;
  is_ready: boolean;
  missing_symbols: string[];
  data_from: string;
  data_to: string;
  data_from_sqx: string;
  data_to_sqx: string;
}

export interface StockGroupDataUpdateResponse {
  group_id: string | number;
  group_name: string;
  status: string;
  message: string;
  total_stocks: number;
  distinct_symbols: number;
  symbols: string[];
}

let client: DomainClient = createDomainClient('/data');

export function setStockGroupApiClient(customClient: DomainClient): void {
  client = customClient;
}

export function toStockGroupDefinition(record: RemoteBasketRecord): StockGroupDefinition {
  return {
    id: String(record.id ?? record.name),
    name: record.name,
    description: record.description || '',
    system: Boolean(record.system),
    members: (record.items || []).map(item => ({
      ticker: item.symbol,
      from: item.date_from || undefined,
      to: item.date_to || undefined,
    })),
  };
}

export function toRemoteBasketPayload(group: StockGroupDefinition): RemoteBasketRecord {
  const isNumeric = /^\d+$/.test(group.id);
  return {
    id: isNumeric ? parseInt(group.id, 10) : undefined,
    name: group.name,
    description: group.description,
    system: group.system,
    items: group.members.map(member => ({
      symbol: member.ticker,
      weight: 1.0,
      date_from: member.from || null,
      date_to: member.to || null,
    })),
  };
}

export async function fetchStockGroups(): Promise<StockGroupDefinition[]> {
  const records = await client.get<RemoteBasketRecord[]>('/baskets');
  return records.map(rec => toStockGroupDefinition(rec));
}

export async function fetchStockGroupsOverview(): Promise<StockGroupOverviewItem[]> {
  return client.get<StockGroupOverviewItem[]>('/baskets/overview');
}

export async function getStockGroup(name: string): Promise<StockGroupDefinition> {
  const record = await client.get<RemoteBasketRecord>(`/baskets/${encodeURIComponent(name)}`);
  return toStockGroupDefinition(record);
}

export async function saveStockGroup(group: StockGroupDefinition): Promise<void> {
  const payload = toRemoteBasketPayload(group);
  await client.post('/baskets', payload);
}

export async function deleteStockGroup(name: string): Promise<void> {
  await client.delete(`/baskets/${encodeURIComponent(name)}`);
}

export async function updateStockGroupsData(
  groupIds: Array<string | number>
): Promise<StockGroupDataUpdateResponse[]> {
  return client.post<StockGroupDataUpdateResponse[]>('/baskets/update-data', {
    basket_ids: groupIds,
  });
}

export async function exportStockGroupsXml(basketNames?: string[]): Promise<string> {
  const resp = await client.post<{ xml_content: string }>('/baskets/export-xml', {
    basket_names: basketNames ?? [],
  });
  return resp.xml_content;
}

export async function importStockGroupsXml(
  xmlContent: string,
  overwrite = false
): Promise<Array<{ id: number; name: string; items: number }>> {
  return client.post<Array<{ id: number; name: string; items: number }>>('/baskets/import-xml', {
    xml_content: xmlContent,
    overwrite,
  });
}

export async function importStockGroupCsv(
  basketName: string,
  csvText: string
): Promise<RemoteBasketRecord> {
  return client.post<RemoteBasketRecord>('/baskets/import-csv', {
    basket_name: basketName,
    csv_text: csvText,
  });
}

export async function exportStockGroupCsv(basketName: string): Promise<string> {
  const resp = await client.get<{ basket_name: string; content: string }>(
    `/baskets/${encodeURIComponent(basketName)}/export-csv`
  );
  return resp.content;
}
