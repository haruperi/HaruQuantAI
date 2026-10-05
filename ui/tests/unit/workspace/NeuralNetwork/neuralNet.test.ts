import { describe, expect, it, beforeEach } from 'vitest';
import { useNeuralNetStore } from '../../../../app/workspace/NeuralNetwork/neuralNetStore';

describe('Neural Network Trainer Workspace Store (FEAT-UI-NEURAL-NETWORK)', () => {
  beforeEach(() => {
    const store = useNeuralNetStore.getState();
    store.stopTraining();
  });

  it('initializes with default model config, layers, and idle status', () => {
    const state = useNeuralNetStore.getState();
    expect(state.status).toBe('idle');
    expect(state.config.layers.length).toBeGreaterThanOrEqual(3);
    expect(state.config.inputFeatures.length).toBeGreaterThan(0);
    expect(state.config.epochs).toBe(50);
    expect(state.config.optimizer).toBe('Adam');
  });

  it('updates hyperparameters correctly', () => {
    const store = useNeuralNetStore.getState();
    store.updateConfig({
      learningRate: 0.0005,
      batchSize: 64,
      optimizer: 'RMSprop',
    });

    const state = useNeuralNetStore.getState();
    expect(state.config.learningRate).toBe(0.0005);
    expect(state.config.batchSize).toBe(64);
    expect(state.config.optimizer).toBe('RMSprop');
  });

  it('adds and removes hidden layers dynamically', () => {
    const store = useNeuralNetStore.getState();
    const initialLayerCount = store.config.layers.length;

    store.addLayer();
    expect(useNeuralNetStore.getState().config.layers.length).toBe(initialLayerCount + 1);

    const added = useNeuralNetStore.getState().config.layers[initialLayerCount - 1];
    expect(added.type).toBe('dense');

    store.removeLayer(added.id);
    expect(useNeuralNetStore.getState().config.layers.length).toBe(initialLayerCount);
  });

  it('modifies layer properties (neurons, activation function)', () => {
    const store = useNeuralNetStore.getState();
    const targetLayer = store.config.layers[0];

    store.updateLayer(targetLayer.id, { neurons: 128, activation: 'Tanh' });

    const updated = useNeuralNetStore.getState().config.layers.find((l) => l.id === targetLayer.id);
    expect(updated?.neurons).toBe(128);
    expect(updated?.activation).toBe('Tanh');
  });

  it('toggles input features', () => {
    const store = useNeuralNetStore.getState();
    const testFeature = 'Volume_Surge_ZScore';

    const initiallyIncluded = store.config.inputFeatures.includes(testFeature);
    store.toggleInputFeature(testFeature);
    expect(useNeuralNetStore.getState().config.inputFeatures.includes(testFeature)).toBe(!initiallyIncluded);

    // Toggle back
    store.toggleInputFeature(testFeature);
    expect(useNeuralNetStore.getState().config.inputFeatures.includes(testFeature)).toBe(initiallyIncluded);
  });

  it('simulates training epoch stepping with loss reduction and accuracy improvement', () => {
    const store = useNeuralNetStore.getState();
    store.updateConfig({ epochs: 10 });
    store.startTraining();

    expect(useNeuralNetStore.getState().status).toBe('training');
    expect(useNeuralNetStore.getState().currentEpoch).toBe(0);

    // Step through 10 epochs
    for (let i = 0; i < 10; i++) {
      useNeuralNetStore.getState().stepEpoch();
    }

    const state = useNeuralNetStore.getState();
    expect(state.status).toBe('completed');
    expect(state.currentEpoch).toBe(10);
    expect(state.history.length).toBe(10);

    const firstEpoch = state.history[0];
    const lastEpoch = state.history[9];

    // Loss should decrease over training
    expect(lastEpoch.loss).toBeLessThan(firstEpoch.loss);
    // Accuracy should increase over training
    expect(lastEpoch.accuracy).toBeGreaterThan(firstEpoch.accuracy);

    // Evaluation metrics should be generated upon completion
    expect(state.evaluation).not.toBeNull();
    expect(state.evaluation?.f1Score).toBeGreaterThan(0.7);
    expect(state.evaluation?.confusionMatrix).toHaveLength(2);
  });

  it('exports generated Java strategy code with feature inputs and forward pass', () => {
    const store = useNeuralNetStore.getState();
    const code = store.generateStrategyCode();

    expect(code).toContain('package HaruQuantAI.Strategies;');
    expect(code).toContain('extends NeuralStrategy');
    expect(code).toContain('model.forward(inputs)');
    expect(code).toContain('enterLong');
    expect(code).toContain('enterShort');
  });
});
