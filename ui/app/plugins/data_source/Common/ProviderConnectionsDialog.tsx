import { useEffect, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../components/ui';
import { createDomainClient } from '../../../host/transport';

export interface ProviderConnection { connection_id: string; name: string; provider: string; endpoint: string; kind: 'broker' | 'exchange'; vault_refs?: Record<string, string> }
const client = createDomainClient('');
const endpoints: Record<string, string> = {darwinex:'https://cdn.strategyquantcdn.com/data/darwinex', sq_equity:'https://cdn.strategyquantcdn.com/data/barchart_test/eod', sq_futures:'https://cdn.strategyquantcdn.com/data/barchart_test/eod', yahoo:'https://query1.finance.yahoo.com', binance:'https://api.binance.com', binance_coinm:'https://dapi.binance.com', binance_usdtm:'https://fapi.binance.com', coinbase:'https://api.exchange.coinbase.com', bitfinex:'https://api-pub.bitfinex.com', poloniex:'https://api.poloniex.com', mt5:'http://127.0.0.1:5555'};

export function ProviderConnectionsDialog({provider, onClose, onSaved}: {provider:string; onClose:()=>void; onSaved:(id:string)=>void}) {
  const [connections, setConnections] = useState<ProviderConnection[]>([]);
  const [id, setId] = useState(''); const [name, setName] = useState(provider);
  const [endpoint, setEndpoint] = useState(endpoints[provider] ?? '');
  const [username, setUsername] = useState(''); const [password, setPassword] = useState('');
  const [apiKey, setApiKey] = useState(''); const [token, setToken] = useState('');
  const [pending, setPending] = useState(false); const [error, setError] = useState('');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  async function loadConnections() { setConnections((await client.get<ProviderConnection[]>('/connections')).filter(row => row.provider === provider)); }
  useEffect(() => { void loadConnections().catch(cause => setError(String(cause))); }, [provider]);
  function choose(value:string) { const saved = connections.find(row => row.connection_id === value); setId(value); setName(saved?.name ?? provider); setEndpoint(saved?.endpoint ?? endpoints[provider] ?? ''); setUsername(''); setPassword(''); setApiKey(''); setToken(''); setResult(null); setError(''); }
  async function saveConnection() {
    setPending(true); setError('');
    try {
      const credentials = Object.fromEntries(Object.entries({username,password,api_key:apiKey,token}).filter(([,value])=>value));
      const payload = {name,provider,endpoint,kind:provider.startsWith('binance') || ['coinbase','bitfinex','poloniex'].includes(provider) ? 'exchange' : 'broker', ...(Object.keys(credentials).length ? {credentials} : {})};
      const saved = id ? await client.put<ProviderConnection>(`/connections/${encodeURIComponent(id)}`,payload) : await client.post<ProviderConnection>('/connections',payload);
      setPassword(''); setApiKey(''); setToken(''); setUsername(''); setId(saved.connection_id);
      await loadConnections(); onSaved(saved.connection_id);
    } catch(cause) {setError(cause instanceof Error ? cause.message : 'Connection could not be saved.');}
    finally {setPending(false);}
  }
  async function testConnection() {
    if (!id) {setError('Save the connection before testing.'); return;}
    setPending(true); setError(''); setResult(null);
    try {setResult(await client.post(`/connections/${encodeURIComponent(id)}/test`,{}));}
    catch(cause) {setError(cause instanceof Error ? cause.message : 'Provider access could not be verified.');}
    finally {setPending(false);}
  }
  async function remove() {setPending(true); setError(''); try {await client.delete(`/connections/${encodeURIComponent(id)}`); choose(''); await loadConnections(); onSaved('');} catch(cause) {setError(String(cause));} finally {setPending(false);}}
  return <Modal title={`${provider} connections`} width={600} onClose={onClose} footer={<><Button disabled={pending} onClick={onClose}>Close</Button><Button disabled={pending || !id} onClick={() => void testConnection()}>Test access</Button><Button disabled={pending || !id} onClick={() => void remove()}>Remove</Button><Button disabled={pending} onClick={() => void saveConnection()}>Save connection</Button></>}>
    {error && <p role="alert">{error}</p>}
    <Field label="Saved connection"><select value={id} disabled={pending} onChange={event => choose(event.target.value)}><option value="">New connection</option>{connections.map(row => <option key={row.connection_id} value={row.connection_id}>{row.name}</option>)}</select></Field>
    <Field label="Connection name"><TextInput value={name} disabled={pending} onChange={event=>setName(event.target.value)}/></Field>
    <Field label="Provider endpoint"><TextInput value={endpoint} disabled={pending} onChange={event=>setEndpoint(event.target.value)}/></Field>
    <p>Credentials are optional for public history. Enter new values to replace saved credentials; saved secrets are never displayed.</p>
    <Field label="Username"><TextInput autoComplete="off" value={username} disabled={pending} onChange={event=>setUsername(event.target.value)}/></Field>
    <Field label="Password"><TextInput type="password" autoComplete="new-password" value={password} disabled={pending} onChange={event=>setPassword(event.target.value)}/></Field>
    <Field label="API key"><TextInput type="password" value={apiKey} disabled={pending} onChange={event=>setApiKey(event.target.value)}/></Field>
    <Field label="Access token"><TextInput type="password" value={token} disabled={pending} onChange={event=>setToken(event.target.value)}/></Field>
    {result && <section aria-label="Provider access test"><p>Status: {String(result.status)}</p><p>Authentication: {String(result.authentication ?? result.authenticated)}</p><p>Data access: {String(result.entitlement ?? 'unknown')}</p><p>Latency: {String(result.latency_ms ?? 'unavailable')} ms</p></section>}
  </Modal>;
}
