import { createDomainClient } from '../../../host/transport';
import type { ExternalImportFormat, ExternalIndicatorDefinition } from './externalIndicators';
const client = createDomainClient('/contributions/workspace.data_manager');
export interface IndicatorState { revision?: number; definitions: ExternalIndicatorDefinition[]; formats: ExternalImportFormat[] }
let revision: number | undefined;
let saving = false;
export async function indicatorState() {
  const state = await client.post<IndicatorState>('/sources.indicators.state.get', {});
  revision = state.revision; return state;
}
export async function replaceIndicatorState(state: IndicatorState) {
  if (saving) throw new Error('Wait for the current indicator save to finish.');
  saving = true;
  try {
    if (revision === undefined) await indicatorState();
    const response = await client.post<IndicatorState>('/sources.indicators.state.replace', { ...state, revision });
    revision = response.revision; return response;
  } finally { saving = false; }
}
export const importIndicator = (indicator: string, text: string, format: ExternalImportFormat, ignore_errors: boolean) => client.post<{ job_id: string }>('/sources.indicators.import.start', { indicator, text, format, ignore_errors });
export const indicatorJob = (job_id: string) => client.post<{ state: string; rows: number; ignored: number }>('/sources.indicators.import.status', { job_id });
export const cancelIndicator = (job_id: string) => client.post('/sources.indicators.import.cancel', { job_id });
