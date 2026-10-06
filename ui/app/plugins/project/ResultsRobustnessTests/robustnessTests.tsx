import { RobustnessAnalysis } from './directives/robustnessAnalysis/robustnessAnalysis';

export function RobustnessTestsTab({ method, setMethod }: { method: string; setMethod: (value: string) => void }) {
  return <div className="sqr-tab"><div className="sqr-toolbar"><label>Test choice <select value={method} onChange={e => setMethod(e.target.value)}>{['Randomize trades order', 'Randomly skip trades'].map(v => <option key={v}>{v}</option>)}</select></label></div><div className="sqr-content"><RobustnessAnalysis method={method}/><p className="sqd-gen-help">Precomputed local UI fixture. No analysis is executed.</p></div></div>;
}
