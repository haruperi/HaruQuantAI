import type { ReactNode } from 'react';
import { Button, Modal, TextInput } from '../../../../components/ui';
import { useYahooAdd, type YahooCallbacks } from './addPopupCtrl';
import '../style.css';

export function YahooModal({ title, onClose, children, footer, wide = false }: { title: string; onClose: () => void; children: ReactNode; footer: ReactNode; wide?: boolean }) {
  return <div className={`yahoo-flow ${wide ? 'yahoo-wide' : ''}`} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),textarea:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title={title} width={wide ? 900 : 720} onClose={onClose} footer={footer}>{children}</Modal></div>;
}

export function YahooAddDialog(props: YahooCallbacks) {
  const { onClose } = props;
  const { store, symbols, setSymbols, postfix, setPostfix, error, setError, save } = useYahooAdd(props);
  return <YahooModal wide title="Add Yahoo data" onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
    {(error || store.storageError) && <p className="yahoo-error" role="alert">{error || store.storageError}</p>}
    <fieldset className="yahoo-add-fieldset"><legend>Add data to download</legend>
      <div className="yahoo-help"><p>Please enter a list of stocks tickers you want to add, separated by comma, semicolon or newline.</p><p>For example: AAPL, AMZN, TSLA</p></div>
      <textarea aria-label="Yahoo symbols" value={symbols} onChange={event => { setSymbols(event.target.value); setError(''); }} />
    </fieldset>
    <label className="yahoo-postfix">Data postfix <span><TextInput aria-label="Data postfix" maxLength={64} value={postfix} onChange={event => { setPostfix(event.target.value); setError(''); }}/><small>This postfix will be optionally added to the data names created</small></span></label>
    <p className="yahoo-mock-note">Offline mock lookup. No request is sent to Yahoo Finance.</p>
  </YahooModal>;
}
