/** Host login modal and REST client helpers for ConnectionTest and ServletConnection. */

import type { FormEvent } from 'react';
import { Button, Field, Modal, TextInput } from '../components/ui';
import { createDomainClient, type TransportConfig } from './transport';

export interface HostConnectionRecord {
  connection_id?: string;
  name?: string;
  endpoint?: string;
  host?: string;
  updated_at_utc?: string;
  [key: string]: unknown;
}

export interface ConnectionPingResult {
  endpoint: string;
  host: string;
  port: number;
  reachable: boolean;
  latency_ms: number;
  error: string | null;
}

export interface ConnectionTestResult {
  connection_id: string | null;
  endpoint: string;
  test_result: ConnectionPingResult;
  timestamp: string;
}

export async function listHostConnections(
  config: TransportConfig = {},
): Promise<HostConnectionRecord[]> {
  const response = await createDomainClient('', config).get<{
    connections: HostConnectionRecord[];
    count: number;
  }>('/connections');
  return Array.isArray(response?.connections) ? response.connections : [];
}

export async function saveHostConnection(
  connection: HostConnectionRecord,
  config: TransportConfig = {},
): Promise<HostConnectionRecord> {
  return createDomainClient('', config).post<HostConnectionRecord>('/connections', connection);
}

export async function deleteHostConnection(
  connectionId: string,
  config: TransportConfig = {},
): Promise<{ connection_id: string; deleted: boolean }> {
  return createDomainClient('', config).delete<{ connection_id: string; deleted: boolean }>(
    `/connections/${encodeURIComponent(connectionId)}`,
  );
}

export async function testHostConnection(
  options: { connectionId?: string; endpoint?: string } = {},
  config: TransportConfig = {},
): Promise<ConnectionTestResult> {
  const path = options.connectionId
    ? `/connections/${encodeURIComponent(options.connectionId)}/test`
    : '/connections/test';
  return createDomainClient('', config).post<ConnectionTestResult>(path, {
    connection_id: options.connectionId,
    endpoint: options.endpoint,
  });
}

export interface HostConnectionModalProps {
  connecting: boolean;
  message: string;
  password: string;
  onPasswordChange: (password: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onClose: () => void;
}

export function HostConnectionModal({
  connecting,
  message,
  password,
  onPasswordChange,
  onSubmit,
  onClose,
}: HostConnectionModalProps) {
  return (
    <Modal
      title="Connect to HaruQuantAI host"
      onClose={onClose}
      footer={
        <Button form="host-login" type="submit" className="primary" disabled={connecting}>
          {connecting ? 'Connecting...' : 'Connect'}
        </Button>
      }
    >
      <form id="host-login" onSubmit={onSubmit}>
        <p role="alert">{message || 'Enter the host password to connect.'}</p>
        <Field label="Host password">
          <TextInput
            type="password"
            required
            maxLength={1024}
            disabled={connecting}
            autoComplete="current-password"
            value={password}
            onChange={event => onPasswordChange(event.target.value)}
          />
        </Field>
      </form>
    </Modal>
  );
}
