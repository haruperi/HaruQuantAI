import { createDomainClient } from '../../../host/transport';
const client = createDomainClient('/contributions/workspace.data_manager');
export interface ClockPolicyResponse {
  revision: number;
  revisions: Record<string, unknown>[];
  database_broker_id: string;
  schema: { properties: Record<string, { type?: string; enum?: unknown[]; format?: string; default?: unknown; minimum?: number; maximum?: number; title?: string }> };
}
export const brokerClockPort = {
  read: (broker_id: string): Promise<ClockPolicyResponse> => client.post('/broker_clock.get', { broker_id }),
  write: (broker_id: string, expected_revision: number, policy: Record<string, unknown>): Promise<ClockPolicyResponse> =>
    client.post('/broker_clock.replace', { broker_id, expected_revision, policy }),
};
export type CatalogKind = 'instruments' | 'sessions' | 'groups' | 'brokers';
export function catalogPort<T extends object>(kind: CatalogKind) {
  let revision = 0; let loaded = false; let busy = false;
  async function read(): Promise<T> {
    const response = await client.post<{ revision: number; state: T }>('/catalogs.get', { kind });
    revision = response.revision; loaded = true; return response.state;
  }
  async function write(state: T): Promise<T> {
    if (busy) throw new Error('Wait for the current catalog save to finish.');
    busy = true;
    try {
      if (!loaded) await read();
      const response = await client.post<{ revision: number; state: T }>('/catalogs.replace', { kind, revision, state });
      revision = response.revision; return response.state;
    } finally { busy = false; }
  }
  return { read, write };
}
