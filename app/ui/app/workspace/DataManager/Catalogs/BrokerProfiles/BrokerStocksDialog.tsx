import { useState } from 'react';
import { Button, Modal } from '../../../../components/ui';
import { parseBrokerStocks, serializeBrokerStocksJson, type BrokerProfile } from './brokerProfiles';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import './brokerProfiles.css';
function download(content: string) { const url = URL.createObjectURL(new Blob([content], { type: 'application/json' })); const a = document.createElement('a'); a.href = url; a.download = 'BrokerStocks.json'; a.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000); }
export function BrokerStocksDialog({ profile, onClose, onSaved }: {
    profile: BrokerProfile;
    onClose: () => void;
    onSaved: (message: string) => void;
}) {
    const [text, setText] = useState(profile.stocks.join('\n'));
    const [error, setError] = useState('');
    const store = useDataManagerStore();
    async function load(file: File | undefined) {
        if (!file)
            return;
        try {
            if (file.size > 1000000)
                throw new Error('Stock file is too large.');
            await store.saveBrokerStocks(profile.id, parseBrokerStocks(await file.text()));
            onSaved('Stocks were imported');
            onClose();
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : 'Cannot import stocks.');
        }
    }
    async function save() {
        try {
            await store.saveBrokerStocks(profile.id, parseBrokerStocks(text));
            onSaved('Stocks were saved.');
            onClose();
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : 'Cannot save stocks.');
        }
    }
    return <div className="broker-flow"><Modal title={`Edit stocks ${profile.name}`} width={700} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
  {error && <p className="broker-error" role="alert">{error}</p>}<p>Use the textarea below to define the individual stocks for broker, separated by lines.<br />Example:</p><pre>AAPL{`\n`}TSLA{`\n`}AMZN</pre><div className="broker-stock-actions"><label className="button">Import from file<input aria-label="Broker stocks file" hidden type="file" accept=".csv,text/csv,text/plain" onChange={async (event) => void await load(event.target.files?.[0])}/></label><Button onClick={() => { download(serializeBrokerStocksJson(parseBrokerStocks(text))); onSaved('Stocks were exported'); onClose(); }}>Export to file</Button></div><textarea className="broker-stocks" aria-label="Broker stocks" value={text} onChange={event => setText(event.target.value)}/>
  </Modal></div>;
}
