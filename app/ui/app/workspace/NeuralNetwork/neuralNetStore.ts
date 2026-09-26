import { create } from 'zustand';
import type {
  NNActivation,
  NNEvaluationMetrics,
  NNLayerConfig,
  NNLossFunction,
  NNOptimizer,
  NNTrainingConfig,
  NNTrainingHistoryPoint,
} from '../../host/types';

interface NeuralNetState {
  config: NNTrainingConfig;
  status: 'idle' | 'training' | 'paused' | 'completed';
  currentEpoch: number;
  history: NNTrainingHistoryPoint[];
  evaluation: NNEvaluationMetrics | null;
  generatedStrategyCode: string | null;

  // Actions
  updateConfig: (patch: Partial<NNTrainingConfig>) => void;
  addLayer: () => void;
  removeLayer: (id: string) => void;
  updateLayer: (id: string, patch: Partial<NNLayerConfig>) => void;
  toggleInputFeature: (feature: string) => void;
  startTraining: () => void;
  pauseTraining: () => void;
  stopTraining: () => void;
  stepEpoch: () => void;
  generateStrategyCode: () => string;
}

const defaultLayers: NNLayerConfig[] = [
  { id: 'layer-1', name: 'Dense Input Projection', type: 'dense', neurons: 64, activation: 'ReLU' },
  { id: 'layer-2', name: 'Hidden Feature Extraction', type: 'dense', neurons: 32, activation: 'ReLU' },
  { id: 'layer-3', name: 'Regularization Dropout', type: 'dropout', neurons: 32, activation: 'Linear', dropoutRate: 0.2 },
  { id: 'layer-4', name: 'Output Classifier', type: 'output', neurons: 3, activation: 'Sigmoid' },
];

const availableFeatures = [
  'EMA_Fast_Cross',
  'RSI_14_Level',
  'ATR_14_Volatility',
  'MACD_Histogram',
  'Bollinger_Band_Width',
  'Volume_Surge_ZScore',
  'Price_Close_Delta_5',
  'Bar_Body_Ratio',
];

const initialConfig: NNTrainingConfig = {
  modelName: 'DeepAlpha-FX-Classifier',
  symbol: 'EURUSD',
  timeframe: 'H1',
  inputFeatures: ['EMA_Fast_Cross', 'RSI_14_Level', 'ATR_14_Volatility', 'MACD_Histogram'],
  layers: defaultLayers,
  epochs: 50,
  batchSize: 32,
  learningRate: 0.001,
  optimizer: 'Adam',
  lossFunction: 'Binary CrossEntropy',
  trainSplit: 60,
  valSplit: 20,
  testSplit: 20,
  earlyStoppingPatience: 8,
};

export const useNeuralNetStore = create<NeuralNetState>((set, get) => ({
  config: initialConfig,
  status: 'idle',
  currentEpoch: 0,
  history: [],
  evaluation: null,
  generatedStrategyCode: null,

  updateConfig: (patch) => set({ config: { ...get().config, ...patch } }),

  addLayer: () => {
    const layers = [...get().config.layers];
    const newId = `layer-${Date.now()}`;
    const insertIndex = Math.max(0, layers.length - 1);
    const newLayer: NNLayerConfig = {
      id: newId,
      name: `Hidden Dense ${layers.length}`,
      type: 'dense',
      neurons: 32,
      activation: 'ReLU',
    };
    layers.splice(insertIndex, 0, newLayer);
    set({ config: { ...get().config, layers } });
  },

  removeLayer: (id: string) => {
    const layers = get().config.layers.filter(l => l.id !== id);
    if (layers.length >= 1) {
      set({ config: { ...get().config, layers } });
    }
  },

  updateLayer: (id: string, patch: Partial<NNLayerConfig>) => {
    set({
      config: {
        ...get().config,
        layers: get().config.layers.map(l => (l.id === id ? { ...l, ...patch } : l)),
      },
    });
  },

  toggleInputFeature: (feature: string) => {
    const current = get().config.inputFeatures;
    const next = current.includes(feature)
      ? current.filter(f => f !== feature)
      : [...current, feature];
    set({ config: { ...get().config, inputFeatures: next } });
  },

  startTraining: () => {
    if (get().status === 'idle' || get().status === 'completed') {
      set({
        status: 'training',
        currentEpoch: 0,
        history: [],
        evaluation: null,
        generatedStrategyCode: null,
      });
    } else {
      set({ status: 'training' });
    }
  },

  pauseTraining: () => set({ status: 'paused' }),

  stopTraining: () => set({ status: 'idle' }),

  stepEpoch: () => {
    const epoch = get().currentEpoch + 1;
    const maxEpochs = get().config.epochs;

    // Deterministic synthetic convergence simulation
    const decay = Math.exp(-epoch / 18);
    const noise = Math.sin(epoch * 1.5) * 0.015;
    const trainLoss = Math.max(0.08, 0.65 * decay + 0.07 + noise);
    const valLoss = Math.max(0.12, 0.68 * decay + 0.11 + noise * 1.3);
    const trainAcc = Math.min(0.96, 0.52 + (1 - decay) * 0.42 - noise * 0.5);
    const valAcc = Math.min(0.89, 0.50 + (1 - decay) * 0.36 - noise * 0.7);

    const nextPoint: NNTrainingHistoryPoint = {
      epoch,
      loss: Number(trainLoss.toFixed(4)),
      valLoss: Number(valLoss.toFixed(4)),
      accuracy: Number(trainAcc.toFixed(4)),
      valAccuracy: Number(valAcc.toFixed(4)),
    };

    const newHistory = [...get().history, nextPoint];

    if (epoch >= maxEpochs) {
      const evaluation: NNEvaluationMetrics = {
        testLoss: Number((valLoss * 1.03).toFixed(4)),
        testAccuracy: Number((valAcc * 0.98).toFixed(4)),
        precision: 0.86,
        recall: 0.83,
        f1Score: 0.845,
        confusionMatrix: [[142, 24], [28, 136]],
      };
      set({
        currentEpoch: epoch,
        history: newHistory,
        status: 'completed',
        evaluation,
      });
    } else {
      set({
        currentEpoch: epoch,
        history: newHistory,
      });
    }
  },

  generateStrategyCode: () => {
    const cfg = get().config;
    const code = `// Model: ${cfg.modelName}
// Architecture: [${cfg.inputFeatures.length} inputs -> ${cfg.layers.map(l => `${l.neurons} (${l.activation})`).join(' -> ')}]
// Timeframe: ${cfg.symbol} ${cfg.timeframe}

package HaruQuantAI.Strategies;

import haruquantai.neural.*;
import haruquantai.indicators.*;

public class ${cfg.modelName.replace(/[^a-zA-Z0-9]/g, '')} extends NeuralStrategy {
    private ModelInstance model;

    @Override
    public void onInit() {
        this.model = NeuralRuntime.loadTrainedWeights("${cfg.modelName}.hqa");
        this.setStopLossPips(45);
        this.setProfitTargetPips(90);
    }

    @Override
    public void onBarUpdate() {
        double[] inputs = new double[] {
${cfg.inputFeatures.map(f => `            getFeature("${f}")`).join(',\n')}
        };

        double[] prediction = this.model.forward(inputs);
        double buyProbability = prediction[0];
        double sellProbability = prediction[1];

        if (buyProbability > 0.70 && !hasOpenPosition()) {
            enterLong("NN_Long_Signal");
        } else if (sellProbability > 0.70 && !hasOpenPosition()) {
            enterShort("NN_Short_Signal");
        }
    }
}`;
    set({ generatedStrategyCode: code });
    return code;
  },
}));
export { availableFeatures };
