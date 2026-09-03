export { NewsWidget } from './NewsWidget';
export {
  NEWS_CATEGORIES,
  NEWS_LANGUAGES,
  CATEGORY_LABELS,
  LANGUAGE_LABELS,
  type NewsCategory,
  type NewsLanguage,
  type NewsWidgetConfig,
  type NewsWidgetProps,
} from './contracts';
export { NewsFeature } from './feature';
export { NEWS_MANIFEST } from './manifest';
export {
  DEFAULT_NEWS_CONFIG,
  newsConfigSchema,
  parseNewsConfig,
  resolveNewsConfig,
  PERSISTED_STATE_SCHEMA_VERSION,
  type NewsConfig,
} from './config';
