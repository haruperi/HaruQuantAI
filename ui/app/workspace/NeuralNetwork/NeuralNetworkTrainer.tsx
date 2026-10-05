import { useEffect, useRef, useState } from 'react';
import {
  Activity,
  ArrowRight,
  Brain,
  CheckCircle2,
  Code2,
  Copy,
  Layers,
  Network,
  Pause,
  Play,
  Plus,
  RotateCcw,
  Sliders,
  Sparkles,
  Trash2,
} from 'lucide-react';
import type { NNActivation, NNLossFunction, NNOptimizer } from './documents';
import { Button, Checkbox, Field, Modal, ProgressBar, Section, Select, Stat, TextInput } from '../../components/ui';
import { availableFeatures, useNeuralNetStore } from './neuralNetStore';

export function NeuralNetworkTrainer() {
  const store = useNeuralNetStore();
  const [tab, setTab] = useState<'architecture' | 'training' | 'evaluation' | 'export'>('architecture');
  const [showExportModal, setShowExportModal] = useState(false);
  const [copied, setCopied] = useState(false);
  const timer = useRef<number | null>(null);

  // Interval training simulation loop
  useEffect(() => {
    if (store.status === 'training') {
      timer.current = window.setInterval(() => {
        store.stepEpoch();
      }, 120);
    } else if (timer.current) {
      clearInterval(timer.current);
    }
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [store.status]);

  const handleCopyCode = () => {
    if (store.generatedStrategyCode) {
      navigator.clipboard.writeText(store.generatedStrategyCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const progressPercent = Math.min(100, Math.round((store.currentEpoch / store.config.epochs) * 100));

  return (
    <div className="neural-net-workspace p-4 space-y-4 max-w-[1600px] mx-auto overflow-y-auto">
      {/* Workspace Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-surface p-4 rounded border border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-primary/10 text-primary">
            <Brain size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold">Neural Network Trainer</h1>
            <span className="text-sm text-muted">
              Deep learning model designer, backprop simulation, and strategy rule generator.
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <nav className="flex items-center rounded border border-border overflow-hidden bg-background">
            {(['architecture', 'training', 'evaluation', 'export'] as const).map(t => (
              <button
                key={t}
                type="button"
                className={`px-3 py-1.5 text-xs font-semibold capitalize ${
                  tab === t ? 'bg-primary text-primary-foreground' : 'text-muted hover:text-foreground'
                }`}
                onClick={() => setTab(t)}
              >
                {t}
              </button>
            ))}
          </nav>

          {store.status === 'training' ? (
            <Button onClick={store.pauseTraining} className="bg-amber-600 hover:bg-amber-700 text-white">
              <Pause size={15} /> Pause
            </Button>
          ) : (
            <Button
              className="primary"
              onClick={() => {
                store.startTraining();
                setTab('training');
              }}
            >
              <Play size={15} /> Start Training
            </Button>
          )}

          <Button
            onClick={() => {
              store.generateStrategyCode();
              setTab('export');
            }}
          >
            <Code2 size={15} /> Export Strategy
          </Button>
        </div>
      </div>

      {/* Model Specifications Strip */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <Stat label="Model Name" value={store.config.modelName} />
        <Stat label="Symbol / TF" value={`${store.config.symbol} · ${store.config.timeframe}`} />
        <Stat label="Input Features" value={store.config.inputFeatures.length} />
        <Stat label="Total Layers" value={store.config.layers.length} />
        <Stat label="Target Epochs" value={store.config.epochs} />
        <Stat
          label="Status"
          value={store.status.toUpperCase()}
          tone={store.status === 'completed' ? 'good' : store.status === 'training' ? 'good' : undefined}
        />
      </div>

      {/* TAB 1: MODEL ARCHITECTURE DESIGNER */}
      {tab === 'architecture' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Left Column: Input Features & Hyperparameters */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-surface p-4 rounded border border-border space-y-3">
              <strong className="text-sm">Input Features Selection</strong>
              <div className="space-y-1 max-h-56 overflow-y-auto">
                {availableFeatures.map(f => (
                  <label
                    key={f}
                    className="flex items-center justify-between p-2 rounded hover:bg-background cursor-pointer text-xs"
                  >
                    <span>{f.replace(/_/g, ' ')}</span>
                    <input
                      type="checkbox"
                      checked={store.config.inputFeatures.includes(f)}
                      onChange={() => store.toggleInputFeature(f)}
                    />
                  </label>
                ))}
              </div>
            </div>

            <div className="bg-surface p-4 rounded border border-border space-y-3">
              <strong className="text-sm">Hyperparameters</strong>
              <div className="grid grid-cols-2 gap-2">
                <Field label="Epochs">
                  <TextInput
                    type="number"
                    value={store.config.epochs}
                    onChange={e => store.updateConfig({ epochs: Number(e.target.value) })}
                  />
                </Field>
                <Field label="Batch Size">
                  <TextInput
                    type="number"
                    value={store.config.batchSize}
                    onChange={e => store.updateConfig({ batchSize: Number(e.target.value) })}
                  />
                </Field>
              </div>

              <Field label="Learning Rate">
                <TextInput
                  type="number"
                  step="0.0001"
                  value={store.config.learningRate}
                  onChange={e => store.updateConfig({ learningRate: Number(e.target.value) })}
                />
              </Field>

              <div className="grid grid-cols-2 gap-2">
                <Field label="Optimizer">
                  <select
                    className="text-input w-full"
                    value={store.config.optimizer}
                    onChange={e => store.updateConfig({ optimizer: e.target.value as NNOptimizer })}
                  >
                    <option>Adam</option>
                    <option>SGD</option>
                    <option>RMSprop</option>
                    <option>AdaGrad</option>
                  </select>
                </Field>
                <Field label="Loss Function">
                  <select
                    className="text-input w-full"
                    value={store.config.lossFunction}
                    onChange={e => store.updateConfig({ lossFunction: e.target.value as NNLossFunction })}
                  >
                    <option>Binary CrossEntropy</option>
                    <option>Mean Squared Error</option>
                    <option>Categorical CrossEntropy</option>
                  </select>
                </Field>
              </div>

              <div className="pt-2 border-t border-border">
                <span className="text-xs font-semibold text-muted block mb-1">Dataset Partitioning</span>
                <div className="flex items-center gap-2 text-xs">
                  <span>Train {store.config.trainSplit}%</span>
                  <span>Val {store.config.valSplit}%</span>
                  <span>Test {store.config.testSplit}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Interactive Layer Graph & Editor */}
          <div className="lg:col-span-2 bg-surface p-4 rounded border border-border space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <div className="flex items-center gap-2">
                <Layers size={16} />
                <strong className="text-sm">Layer Hierarchy & Activations</strong>
              </div>
              <Button onClick={store.addLayer} className="text-xs">
                <Plus size={13} /> Add Hidden Layer
              </Button>
            </div>

            {/* Visual Flow Representation */}
            <div className="flex items-center gap-2 overflow-x-auto p-4 bg-background rounded border border-border/80">
              <div className="p-3 rounded bg-blue-500/10 border border-blue-500/30 text-center min-w-[120px]">
                <strong className="text-xs block text-blue-400">INPUT</strong>
                <span className="text-sm font-bold">{store.config.inputFeatures.length} Nodes</span>
                <span className="text-[10px] text-muted block">Normalized Vector</span>
              </div>
              <ArrowRight size={14} className="text-muted shrink-0" />

              {store.config.layers.map((layer, idx) => (
                <div key={layer.id} className="flex items-center gap-2">
                  <div
                    className={`p-3 rounded border text-center min-w-[130px] ${
                      layer.type === 'output'
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : layer.type === 'dropout'
                        ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                        : 'bg-primary/10 border-primary/30 text-primary'
                    }`}
                  >
                    <strong className="text-xs block">
                      {layer.type === 'output' ? 'OUTPUT' : `L${idx + 1}: ${layer.type.toUpperCase()}`}
                    </strong>
                    <span className="text-sm font-bold">{layer.neurons} Neurons</span>
                    <span className="text-[10px] text-muted block">
                      {layer.type === 'dropout' ? `Drop: ${layer.dropoutRate}` : layer.activation}
                    </span>
                  </div>
                  {idx < store.config.layers.length - 1 && (
                    <ArrowRight size={14} className="text-muted shrink-0" />
                  )}
                </div>
              ))}
            </div>

            {/* Layer Configuration Table */}
            <div className="plain-table-wrap overflow-x-auto">
              <table className="plain-table w-full text-xs">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Layer Name</th>
                    <th>Type</th>
                    <th>Neurons</th>
                    <th>Activation</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {store.config.layers.map((layer, idx) => (
                    <tr key={layer.id}>
                      <td>{idx + 1}</td>
                      <td>
                        <input
                          className="bg-transparent border-b border-border/60 text-xs px-1"
                          value={layer.name}
                          onChange={e => store.updateLayer(layer.id, { name: e.target.value })}
                        />
                      </td>
                      <td>
                        <span className="pill">{layer.type}</span>
                      </td>
                      <td>
                        <input
                          type="number"
                          className="bg-transparent border-b border-border/60 text-xs px-1 w-16"
                          value={layer.neurons}
                          onChange={e => store.updateLayer(layer.id, { neurons: Number(e.target.value) })}
                        />
                      </td>
                      <td>
                        <select
                          className="text-input text-xs py-0.5"
                          value={layer.activation}
                          onChange={e => store.updateLayer(layer.id, { activation: e.target.value as NNActivation })}
                        >
                          <option>ReLU</option>
                          <option>LeakyReLU</option>
                          <option>Sigmoid</option>
                          <option>Tanh</option>
                          <option>Linear</option>
                          <option>ELU</option>
                        </select>
                      </td>
                      <td>
                        {layer.type !== 'output' && store.config.layers.length > 2 && (
                          <button
                            type="button"
                            className="text-red-400 hover:text-red-300 p-1"
                            onClick={() => store.removeLayer(layer.id)}
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: TRAINING PROGRESS MONITOR */}
      {tab === 'training' && (
        <div className="space-y-4">
          <div className="bg-surface p-4 rounded border border-border space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <strong className="text-sm">Live Backpropagation Training Loop</strong>
                <p className="text-xs text-muted">
                  Epoch {store.currentEpoch} of {store.config.epochs} · Optimizer: {store.config.optimizer} (LR: {store.config.learningRate})
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold">{progressPercent}%</span>
              </div>
            </div>

            <ProgressBar value={progressPercent} />

            {/* Dual Training Curves (Loss & Accuracy) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              {/* Loss Curve */}
              <div className="p-3 bg-background rounded border border-border space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <strong className="text-red-400">Loss vs Epoch</strong>
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="flex items-center gap-1"><i className="w-2 h-2 rounded-full bg-red-400" /> Train Loss</span>
                    <span className="flex items-center gap-1"><i className="w-2 h-2 rounded-full bg-amber-400" /> Val Loss</span>
                  </div>
                </div>
                <div className="h-44 w-full flex items-end gap-1 pt-4 pb-2 px-1 border-b border-l border-border relative">
                  {store.history.slice(-30).map((h, i) => (
                    <div key={h.epoch} className="flex-1 flex flex-col justify-end items-center h-full gap-0.5">
                      <div
                        className="w-full bg-red-500/80 rounded-t"
                        style={{ height: `${Math.min(100, Math.max(8, h.loss * 120))}%` }}
                        title={`Epoch ${h.epoch} Loss: ${h.loss}`}
                      />
                    </div>
                  ))}
                </div>
                <div className="flex justify-between text-[10px] text-muted">
                  <span>Current Loss: {store.history.at(-1)?.loss ?? '0.0000'}</span>
                  <span>Validation: {store.history.at(-1)?.valLoss ?? '0.0000'}</span>
                </div>
              </div>

              {/* Accuracy Curve */}
              <div className="p-3 bg-background rounded border border-border space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <strong className="text-emerald-400">Accuracy vs Epoch</strong>
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="flex items-center gap-1"><i className="w-2 h-2 rounded-full bg-emerald-400" /> Train Acc</span>
                    <span className="flex items-center gap-1"><i className="w-2 h-2 rounded-full bg-blue-400" /> Val Acc</span>
                  </div>
                </div>
                <div className="h-44 w-full flex items-end gap-1 pt-4 pb-2 px-1 border-b border-l border-border relative">
                  {store.history.slice(-30).map((h, i) => (
                    <div key={h.epoch} className="flex-1 flex flex-col justify-end items-center h-full gap-0.5">
                      <div
                        className="w-full bg-emerald-500/80 rounded-t"
                        style={{ height: `${Math.min(100, Math.max(8, (h.accuracy - 0.4) * 160))}%` }}
                        title={`Epoch ${h.epoch} Accuracy: ${(h.accuracy * 100).toFixed(1)}%`}
                      />
                    </div>
                  ))}
                </div>
                <div className="flex justify-between text-[10px] text-muted">
                  <span>Train Accuracy: {((store.history.at(-1)?.accuracy ?? 0) * 100).toFixed(1)}%</span>
                  <span>Val Accuracy: {((store.history.at(-1)?.valAccuracy ?? 0) * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: EVALUATION & CONFUSION MATRIX */}
      {tab === 'evaluation' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-surface p-4 rounded border border-border space-y-3">
            <strong className="text-sm">Model Generalization Metrics (Test Split)</strong>
            <dl className="details">
              <dt>Test Accuracy</dt>
              <dd className="font-bold text-emerald-400">
                {store.evaluation ? `${(store.evaluation.testAccuracy * 100).toFixed(2)}%` : 'Train model to view'}
              </dd>
              <dt>Test Loss</dt>
              <dd>{store.evaluation?.testLoss ?? '—'}</dd>
              <dt>Precision</dt>
              <dd>{store.evaluation ? (store.evaluation.precision * 100).toFixed(1) + '%' : '—'}</dd>
              <dt>Recall</dt>
              <dd>{store.evaluation ? (store.evaluation.recall * 100).toFixed(1) + '%' : '—'}</dd>
              <dt>F1-Score</dt>
              <dd className="font-bold">{store.evaluation?.f1Score ?? '—'}</dd>
            </dl>
          </div>

          <div className="bg-surface p-4 rounded border border-border space-y-3">
            <strong className="text-sm">Binary Classification Confusion Matrix</strong>
            <table className="mini-table w-full text-center">
              <thead>
                <tr>
                  <th>Actual \ Predicted</th>
                  <th>Predicted Long</th>
                  <th>Predicted Short</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Actual Long</strong></td>
                  <td className="bg-emerald-500/10 font-bold text-emerald-400">
                    {store.evaluation?.confusionMatrix[0][0] ?? 142} (TP)
                  </td>
                  <td className="bg-red-500/10 text-red-400">
                    {store.evaluation?.confusionMatrix[0][1] ?? 24} (FN)
                  </td>
                </tr>
                <tr>
                  <td><strong>Actual Short</strong></td>
                  <td className="bg-red-500/10 text-red-400">
                    {store.evaluation?.confusionMatrix[1][0] ?? 28} (FP)
                  </td>
                  <td className="bg-emerald-500/10 font-bold text-emerald-400">
                    {store.evaluation?.confusionMatrix[1][1] ?? 136} (TN)
                  </td>
                </tr>
              </tbody>
            </table>
            <p className="text-xs text-muted">
              Evaluated on 330 unseen Out-of-Sample bars.
            </p>
          </div>
        </div>
      )}

      {/* TAB 4: EXPORT TO STRATEGY */}
      {tab === 'export' && (
        <div className="bg-surface p-4 rounded border border-border space-y-3">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <div>
              <strong className="text-sm">StrategyQuant Rule & Code Integration</strong>
              <p className="text-xs text-muted">
                Export trained neural network model into executable strategy rules.
              </p>
            </div>
            <Button onClick={handleCopyCode}>
              <Copy size={14} /> {copied ? 'Copied!' : 'Copy Code'}
            </Button>
          </div>

          <pre className="code-block text-xs font-mono p-3 bg-background rounded border border-border overflow-x-auto max-h-96">
            {store.generatedStrategyCode ?? store.generateStrategyCode()}
          </pre>
        </div>
      )}
    </div>
  );
}
export { NeuralNetworkTrainer as NeuralNetWorkspace };
