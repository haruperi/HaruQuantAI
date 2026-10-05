import type { UIContribution } from '../../host/contributions';
import { BrainCircuit } from 'lucide-react';
export const contribution: UIContribution = { id:'workspace.neural_network', kind:'workspace', version:'1.0.0', slots:[],
navigation: { id:'neuralnet', path:'/neuralnet', aliases:[], label:"Neural Network", icon:BrainCircuit, order:7, hidden:false, home:false },
load: async () => ({ View: (await import('./NeuralNetworkTrainer')).NeuralNetworkTrainer }),
};
