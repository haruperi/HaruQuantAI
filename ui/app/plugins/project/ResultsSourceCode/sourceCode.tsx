import { downloadText, type ResultDocument } from '../ProjectWorkbench/results/resultsModel';
import { useSourceCode } from './SourceCodeCtrl';
import { RefreshCw } from 'lucide-react';
import { SqrDropdown } from '../ProjectWorkbench/results/ResultsChrome';
import { SqdCheckbox, SqdRadio } from '../ProjectWorkbench/settings/SettingsControls';
import { sourceCodeDescriptions, sourceCodeGenerators, sourceCodeMmTypes, } from '../ProjectWorkbench/results/resultsFixtures';
/** Source Code tab: generator select, save/copy buttons, variables menu, code area. */
export function SourceCodeTab({ result }: {
    result: ResultDocument | null;
}) {
    const { copyError, setRevision, type, setType, mmType, setMmType, config, set, varsOpen, setVarsOpen, copied, code, onCopy } = useSourceCode(result);
    return (<div className="sqr-tab sqr-sourcecode">
      <div className="sqr-sourcecode-form">
        <label>Source code type</label>
        <span className="sqd-select sqr-sourcecode-select">
          <span>{type}</span>
          <select aria-label="Source code type" value={type} onChange={e => setType(e.target.value)}>
            {sourceCodeGenerators.map(g => (<option key={g} value={g}>{g}</option>))}
          </select>
        </span>
        <button type="button" className="sqd-btn" disabled={!result} onClick={() => downloadText("strategy-preview.txt", code)}>Save to file</button>
        <button type="button" className="sqd-btn" disabled={!result} onClick={onCopy}>Copy to clipboard</button>
        <a role="button" tabIndex={0} className="sqr-refresh-link" title="Refresh" aria-label="Refresh source code" onClick={() => setRevision(r => r + 1)} onKeyDown={e => e.key === 'Enter' && setRevision(r => r + 1)}>
          <RefreshCw size={12}/>
        </a>
        {copied && <span className="sqr-copied">Copied to clipboard</span>}
        <span className="sqr-sourcecode-right">
          <span className="sqr-vars-dd">
            <a role="button" tabIndex={0} title="Settings" onClick={() => setVarsOpen(v => !v)} onKeyDown={e => e.key === 'Enter' && setVarsOpen(v => !v)}>
              Parameter variables
            </a>
            <SqrDropdown open={varsOpen} onClose={() => setVarsOpen(false)} className="sqr-vars-menu">
              <strong>What to parametrize</strong>
              <div className="sqr-vars-radios">
                <div className="radio">
                  <SqdRadio name="sqr-what-to-parametrize" value="recommended" checked={config.parametrizeType === 0} onChange={() => set('parametrizeType', 0)}>
                    <span className="sqr-wradio-line">
                      Recommended parameters
                      <span className="sqr-data-help">
                        Only meaningful parameters. It is not a good idea to optimize everything
                        <br />
                        Recommended params are: periods, entry + exit settings &amp; multipliers
                      </span>
                    </span>
                  </SqdRadio>
                </div>
                <div className="radio">
                  <SqdRadio name="sqr-what-to-parametrize" value="own" checked={config.parametrizeType === 1} onChange={() => set('parametrizeType', 1)}>
                    <span className="sqr-wradio-line">
                      Your own settings
                      <span className="sqr-data-help">Choose your own categories</span>
                    </span>
                  </SqdRadio>
                  {config.parametrizeType === 1 && (<div className="sqr-vars-categories">
                      <div className="sqr-vars-col">
                        <SqdCheckbox checked={config.periodParams} onChange={v => set('periodParams', v)}>Periods</SqdCheckbox>
                        <SqdCheckbox checked={config.constantsParams} onChange={v => set('constantsParams', v)}>Constants</SqdCheckbox>
                        <SqdCheckbox checked={config.shiftParams} onChange={v => set('shiftParams', v)}>Shifts</SqdCheckbox>
                        <SqdCheckbox checked={config.otherParams} onChange={v => set('otherParams', v)}>Other params</SqdCheckbox>
                      </div>
                      <div className="sqr-vars-col">
                        <SqdCheckbox checked={config.entryParams} onChange={v => set('entryParams', v)}>Entry (levels)</SqdCheckbox>
                        <SqdCheckbox checked={config.entryLogic} onChange={v => set('entryLogic', v)}>Entry (logic)</SqdCheckbox>
                        <SqdCheckbox checked={config.exitParamsUsed} onChange={v => set('exitParamsUsed', v)}>Exit params (SL, PT,...) only used</SqdCheckbox>
                        <SqdCheckbox checked={config.exitParamsUnused} onChange={v => set('exitParamsUnused', v)}>Exit params (SL, PT,...) unused</SqdCheckbox>
                        <SqdCheckbox checked={config.booleanParams} onChange={v => set('booleanParams', v)}>Boolean params</SqdCheckbox>
                      </div>
                      <div className="sqr-vars-col sqr-vars-col-full">
                        <hr />
                        <SqdCheckbox checked={config.symmetricVariables} onChange={v => set('symmetricVariables', v)}>Symmetric variables for Long / Short</SqdCheckbox>
                      </div>
                    </div>)}
                </div>
                <div className="radio">
                  <SqdRadio name="sqr-what-to-parametrize" value="none" checked={config.parametrizeType === 2} onChange={() => set('parametrizeType', 2)}>
                    Don&apos;t use parameters
                  </SqdRadio>
                </div>
              </div>
            </SqrDropdown>
          </span>
          <label>MM used</label>
          <span className="sqd-select">
            <span>{sourceCodeMmTypes.find(m => m.value === mmType)?.label ?? mmType}</span>
            <select aria-label="MM used" value={mmType} onChange={e => setMmType(e.target.value)}>
              {sourceCodeMmTypes.map(m => (<option key={m.value} value={m.value}>{m.label}</option>))}
            </select>
          </span>
        </span>
      </div>
      <div className="sqr-sourcecode-desc">{sourceCodeDescriptions[type] ?? ''}</div>
      {copyError && <p role="alert">{copyError}</p>}<pre className="sqr-sourcecode-editor" aria-label="Source code">{code}</pre>
    </div>);
}
