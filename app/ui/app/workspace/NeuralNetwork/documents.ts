/** Owner-local presentation/resource documents; no backend execution authority. */
export type NNActivation = 'ReLU' | 'LeakyReLU' | 'Sigmoid' | 'Tanh' | 'Linear' | 'ELU';

export type NNLossFunction = 'Mean Squared Error' | 'Binary CrossEntropy' | 'Categorical CrossEntropy';

export type NNOptimizer = 'Adam' | 'SGD' | 'RMSprop' | 'AdaGrad';

export interface NNEvaluationMetrics {
  testLoss: number;
  testAccuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  confusionMatrix: [[number, number], [number, number]];
}

export interface NNLayerConfig {
  id: string;
  name: string;
  type: 'input' | 'dense' | 'dropout' | 'output';
  neurons: number;
  activation: NNActivation;
  dropoutRate?: number;
}

export interface NNTrainingConfig {
  modelName: string;
  symbol: string;
  timeframe: string;
  inputFeatures: string[];
  layers: NNLayerConfig[];
  epochs: number;
  batchSize: number;
  learningRate: number;
  optimizer: NNOptimizer;
  lossFunction: NNLossFunction;
  trainSplit: number;
  valSplit: number;
  testSplit: number;
  earlyStoppingPatience: number;
}

export interface NNTrainingHistoryPoint {
  epoch: number;
  loss: number;
  valLoss: number;
  accuracy: number;
  valAccuracy: number;
}
