import { useState } from 'react';
import { FileCode2, Play, Save, TestTube2 } from 'lucide-react';
import { Button } from '../../components/ui';
import { useAppStore } from '../../app/store';

export function CodeEditorWorkspace() {
  const notify = useAppStore(s => s.notify);
  const [file, setFile] = useState('CustomIndicator.java');
  return (
    <div className="code-editor">
      <aside>
        <div className="tree-title">
          <strong>Extensions</strong>
          <Button>＋</Button>
        </div>
        {['Snippets', 'Blocks', 'Indicators', 'Columns', 'CustomAnalysis', 'ResultsPlugins'].map(x => (
          <div className="file-group" key={x}>
            <strong>▾ {x}</strong>
            {[`${x}Example.java`, `Custom${x}.java`].map(f => (
              <button key={f} className={file === f ? 'active' : ''} onClick={() => setFile(f)}>
                <FileCode2 size={14}/>
                {f}
              </button>
            ))}
          </div>
        ))}
      </aside>
      <main>
        <div className="editor-tabs">
          <button>{file} ×</button>
        </div>
        <div className="editor-toolbar">
          <Button onClick={() => notify('Source saved to the browser-backed mock workspace')}>
            <Save size={14}/>Save
          </Button>
          <Button onClick={() => notify('Mock compile passed; no native compiler was invoked')}>
            <Play size={14}/>Compile
          </Button>
          <Button>
            <TestTube2 size={14}/>Test
          </Button>
          <span>Mock editor · compilation is simulated</span>
        </div>
        <pre className="monaco-mock">
          <code>
            <i>1</i>package HaruQuantAI.Blocks;{'\n'}
            <i>2</i>{'\n'}
            <i>3</i>import haruquantai.lib.*;{'\n'}
            <i>4</i>{'\n'}
            <i>5</i><b>public class</b> CustomIndicator {'{'}{'\n'}
            <i>6</i>  <b>public double</b> calculate(<b>int</b> period) {'{'}{'\n'}
            <i>7</i>    <b>return</b> SMA(Chart, PRICE_CLOSE, period);{'\n'}
            <i>8</i>  {'}'}{'\n'}
            <i>9</i>{'}'}
          </code>
        </pre>
        <div className="console">
          <strong>Build output</strong>
          <p>[mock] Validation completed with 0 errors and 0 warnings.</p>
        </div>
      </main>
    </div>
  );
}
export { CodeEditorWorkspace as CodeEditor };
