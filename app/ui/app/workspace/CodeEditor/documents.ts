/** Owner-local presentation/resource documents; no backend execution authority. */
export interface ExtensionFile {
  id: string;
  name: string;
  category: 'Snippets' | 'Blocks' | 'Indicators' | 'Columns' | 'CustomAnalysis' | 'ResultsPlugins';
  language: 'java' | 'python';
  content: string;
  dirty?: boolean;
}
