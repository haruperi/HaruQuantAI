import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SessionRegistryWidget } from './SessionRegistryWidget';

const {
  listExecutionSessions,
  createExecutionSession,
  actOnExecutionSession,
  updateExecutionSession,
  executionSessionEvents,
  executionSessionActivity,
  completeExecutionSessionConfiguration,
  datasets,
} = vi.hoisted(() => ({
  listExecutionSessions: vi.fn(),
  createExecutionSession: vi.fn(),
  actOnExecutionSession: vi.fn(),
  updateExecutionSession: vi.fn(),
  executionSessionEvents: vi.fn(),
  executionSessionActivity: vi.fn(),
  completeExecutionSessionConfiguration: vi.fn(),
  datasets: vi.fn(),
}));

vi.mock('@/clients', () => ({
  apiClients: { trading: {
    listExecutionSessions,
    createExecutionSession,
    actOnExecutionSession,
    updateExecutionSession,
    executionSessionEvents,
    executionSessionActivity,
    completeExecutionSessionConfiguration,
  }, data: { datasets } },
  unwrapData: (response: { data: unknown }) => response.data,
}));

describe('SessionRegistryWidget — FR-UI-212 through FR-UI-224', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listExecutionSessions.mockResolvedValue({ data: [] });
    executionSessionEvents.mockResolvedValue({ data: [] });
    executionSessionActivity.mockImplementation(async function* () { return; });
    datasets.mockResolvedValue({ data: [{
      dataset_id: 'dataset-1', label: 'EURUSD H1', dataset_kind: 'historical',
      symbol: 'EURUSD', timeframe: 'H1', revision: 'revision-1', content_hash: 'a'.repeat(64),
      row_count: 1000, active: true,
    }] });
    completeExecutionSessionConfiguration.mockResolvedValue({ data: {} });
  });

  it('renders the empty state and creates a mode-specific session', async () => {
    createExecutionSession.mockResolvedValue({ data: {} });
    render(<SessionRegistryWidget />);
    expect(await screen.findByText('No trading sessions yet')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'New session' }));
    fireEvent.change(screen.getByLabelText('Session name'), { target: { value: 'Demo A' } });
    fireEvent.change(screen.getByLabelText('Mode'), { target: { value: 'demo' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create session' }));
    await waitFor(() => expect(createExecutionSession).toHaveBeenCalledWith({
      name: 'Demo A', description: '', mode: 'demo', provider: 'mt5',
      sim_initial_balance: null, sim_leverage: null, sim_account_currency: null,
      dataset_ref: null, dataset_revision: null, dataset_hash: null,
    }));
  });

  it('shows explicit lifecycle controls for a registered session', async () => {
    listExecutionSessions.mockResolvedValue({ data: [{
      session_id: 'session-1', principal_id: 'person-1', environment_id: 'dev',
      name: 'Demo Alpha', description: 'Verification environment', mode: 'demo',
      provider: 'mt5', provider_account_ref: null, credential_ref: null,
      simulation_session_id: null, dataset_ref: null, dataset_revision: null,
      sim_sequence: null, simulation_runtime_ref: null,
      dataset_hash: null, lifecycle_state: 'stopped', recovery_state: 'not_required',
      sim_initial_balance: null, sim_leverage: null, sim_account_currency: null,
      is_default: false, is_active: false, auto_start: true, metadata: {},
      last_error_code: null, last_reconciled_at: null, started_at: null,
      stopped_at: null, archived_at: null, version: 0,
      created_at: '2026-08-17T00:00:00Z', updated_at: '2026-08-17T00:00:00Z',
    }] });
    render(<SessionRegistryWidget />);
    expect(await screen.findByRole('button', { name: 'Start session' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Make default' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Archive' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Edit session' })).toBeEnabled();
  });

  it('collects opening balance, leverage, and currency only for SIM', async () => {
    createExecutionSession.mockResolvedValue({ data: { session_id: 'sim-new' } });
    render(<SessionRegistryWidget />);
    await screen.findByText('No trading sessions yet');
    fireEvent.click(screen.getByRole('button', { name: 'New session' }));
    fireEvent.change(screen.getByLabelText('Session name'), { target: { value: 'SIM Lab' } });
    fireEvent.change(screen.getByLabelText('Initial balance'), { target: { value: '25000' } });
    fireEvent.change(screen.getByLabelText('Leverage'), { target: { value: '50' } });
    fireEvent.change(screen.getByLabelText('Account currency'), { target: { value: 'eur' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create session' }));
    await waitFor(() => expect(createExecutionSession).toHaveBeenCalledWith(expect.objectContaining({
      mode: 'sim', sim_initial_balance: '25000', sim_leverage: 50,
      sim_account_currency: 'EUR',
      dataset_ref: 'dataset-1', dataset_revision: 'revision-1', dataset_hash: 'a'.repeat(64),
    })));
  });

  it('renders unavailable state without inventing session values', async () => {
    listExecutionSessions.mockRejectedValue(new Error('Registry unavailable'));
    render(<SessionRegistryWidget />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Registry unavailable');
  });

  it('completes stopped legacy SIM setup from an explicitly selected dataset', async () => {
    const legacy = {
      session_id: 'legacy-1', principal_id: 'usr_haruquantai', environment_id: 'dev',
      name: 'Test 2', description: '', mode: 'sim', provider: 'simulation',
      provider_account_ref: null, credential_ref: null, simulation_session_id: null,
      sim_sequence: null, simulation_runtime_ref: null, dataset_ref: null,
      dataset_revision: null, dataset_hash: null, lifecycle_state: 'stopped',
      recovery_state: 'not_required', sim_initial_balance: '100000', sim_leverage: 100,
      sim_account_currency: 'USD', is_default: false, is_active: false, auto_start: true,
      metadata: {}, last_error_code: null, last_reconciled_at: null, started_at: null,
      stopped_at: null, archived_at: null, version: 3,
      created_at: '2026-08-17T00:00:00Z', updated_at: '2026-08-17T00:00:00Z',
    };
    listExecutionSessions.mockResolvedValue({ data: [legacy] });
    render(<SessionRegistryWidget />);

    fireEvent.click(await screen.findByRole('button', { name: 'Complete SIM setup' }));

    await waitFor(() => expect(completeExecutionSessionConfiguration).toHaveBeenCalledWith(
      legacy,
      expect.objectContaining({ dataset_id: 'dataset-1' }),
    ));
  });
});
