import { useEffect, useRef, useState } from 'react';
import type { ResultDocument } from '../ProjectWorkbench/results/resultsModel';
import { sourceCodeGenerators, sourceCodeMmTypes, sourceCodeParamsDefaults, type SourceCodeParamsConfig } from '../ProjectWorkbench/results/resultsFixtures';

/** Current mock code preview and bounded clipboard feedback lifetime. */
export function useSourceCode(result: ResultDocument | null) {
    const [copyError, setCopyError] = useState("");
    const [revision, setRevision] = useState(0);
    const [type, setType] = useState(sourceCodeGenerators[0]);
    const [mmType, setMmType] = useState(sourceCodeMmTypes[0].value);
    const [config, setConfig] = useState<SourceCodeParamsConfig>(sourceCodeParamsDefaults);
    const [varsOpen, setVarsOpen] = useState(false);
    const [copied, setCopied] = useState(false);
    const copyTimer = useRef<number | undefined>(undefined);
    useEffect(() => () => window.clearTimeout(copyTimer.current), []);
    const set = <K extends keyof SourceCodeParamsConfig>(key: K, value: SourceCodeParamsConfig[K]) => setConfig(c => ({ ...c, [key]: value }));
    const code = result ? `// Local mock preview; not executable trading code
// ${result.name}
// Format: ${type}
// Money management: ${mmType}
// Parameters: ${JSON.stringify(config)}
// Revision: ${revision}
IF fast moving average crosses above slow moving average
THEN enter long on next bar` : '';
    const onCopy = async () => {
        try {
            await navigator.clipboard.writeText(code);
            setCopyError('');
        }
        catch {
            setCopyError('Clipboard access unavailable. Select the preview and copy manually.');
            return;
        }
        setCopied(true);
        window.clearTimeout(copyTimer.current);
        copyTimer.current = window.setTimeout(() => setCopied(false), 2500);
    };
    return { copyError, revision, setRevision, type, setType, mmType, setMmType, config, set, varsOpen, setVarsOpen, copied, code, onCopy };
}
