/** Isolate the previous server vocabulary while UI models consistently use symbols. */
import { createDomainClient, type DomainClient, type TransportConfig } from '../../../../shell/transport';

const incoming = new Map([
  ['instrument', 'symbolDefinition'], ['instruments', 'symbols'],
  ['instrument_ids', 'symbol_ids'], ['instruments_count', 'symbols_count'],
  ['customized_instruments', 'customized_symbols'], ['total_instruments', 'total_symbols'],
]);

/** Read both previous saved UI documents and existing host responses. */
export function normalizeSymbolContract<T>(value: T, key = ''): T {
  if (Array.isArray(value)) return value.map(item => normalizeSymbolContract(item)) as T;
  if (value && typeof value === 'object') return Object.fromEntries(
    Object.entries(value).map(([name, item]) => {
      const renamed = incoming.get(name) ?? name;
      return [renamed, normalizeSymbolContract(item, renamed)];
    }),
  ) as T;
  if (value === 'instruments' && ['id', 'active_tab', 'kind'].includes(key)) return 'symbols' as T;
  if (value === 'Instruments' && key === 'title') return 'Symbols' as T;
  return value;
}

function hostBody(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(hostBody);
  if (value && typeof value === 'object') {
    const catalogue = 'kind' in value && value.kind === 'symbols';
    return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [
      key === 'symbolDefinition' ? 'instrument' : key === 'symbol_ids' ? 'instrument_ids' : catalogue && key === 'symbols' ? 'instruments' : key,
      catalogue && key === 'kind' ? 'instruments' : hostBody(item),
    ]),
  );
  }
  return value;
}

/** Preserve existing server routes; new UI clients and injectable fakes use symbols. */
export function createSymbolDataClient(base: string, config: TransportConfig = {}): DomainClient {
  const client = createDomainClient(base, config);
  const path = (value: string) => value.replace(/\/symbols(?=\/|\?|$)/g, '/instruments').replace('/import-symbols', '/import-instruments');
  const result = <T>(value: unknown): T => normalizeSymbolContract(value) as T;
  return {
    get: async <T>(url: string) => result<T>(await client.get(path(url))),
    post: async <T>(url: string, body: unknown) => result<T>(await client.post(path(url), hostBody(body))),
    put: async <T>(url: string, body: unknown) => result<T>(await client.put(path(url), hostBody(body))),
    delete: async <T>(url: string) => result<T>(await client.delete(path(url))),
  };
}
