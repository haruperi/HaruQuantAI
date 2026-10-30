import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { NeuralNetworkWorkspace } from '../../../workspaces/neural_network/NeuralNetworkWorkspace';

describe('AppNeuralNetworkPanel workspace component (FEAT-NEURAL-NETWORK)', () => {
  it('renders complete donor layout with header, tabs, specifications, and architecture panel', () => {
    const html = renderToString(<NeuralNetworkWorkspace />);

    // Container and header
    expect(html).toContain('data-testid="neural-network-workspace"');
    expect(html).toContain('Neural Network Trainer');
    expect(html).toContain('Deep learning model designer');

    // Navigation tabs
    expect(html).toContain('data-testid="tab-architecture"');
    expect(html).toContain('data-testid="tab-training"');
    expect(html).toContain('data-testid="tab-evaluation"');
    expect(html).toContain('data-testid="tab-export"');

    // Action buttons
    expect(html).toContain('data-testid="button-start-training"');
    expect(html).toContain('data-testid="button-export-strategy"');

    // Model specifications strip
    expect(html).toContain('data-testid="model-specs-strip"');
    expect(html).toContain('DeepAlpha-FX-Classifier');
    expect(html).toContain('EURUSD · H1');

    // Architecture panel components
    expect(html).toContain('data-testid="architecture-panel"');
    expect(html).toContain('data-testid="input-features-selection"');
    expect(html).toContain('data-testid="hyperparameters-section"');
    expect(html).toContain('data-testid="layer-hierarchy"');
  });

  it('renders default input features and layer topology in architecture view', () => {
    const html = renderToString(<NeuralNetworkWorkspace />);

    // Selected feature checks
    expect(html).toContain('EMA Fast Cross');
    expect(html).toContain('RSI 14 Level');

    // Layer checks
    expect(html).toContain('Dense Input Projection');
    expect(html).toContain('Hidden Feature Extraction');
    expect(html).toContain('Regularization Dropout');
    expect(html).toContain('Output Classifier');
    expect(html).toContain('ReLU');
    expect(html).toContain('Sigmoid');
  });
});
