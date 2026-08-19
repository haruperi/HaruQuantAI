/**
 * Contracts and constants for the News Online Feed Widget (FEAT-UI-29).
 */

export const NEWS_CATEGORIES = [
  'finance',
  'forex',
  'stocks',
  'company_news',
  'commodities',
] as const;

export type NewsCategory = (typeof NEWS_CATEGORIES)[number];

export const CATEGORY_LABELS: Record<NewsCategory, string> = {
  finance: 'Finance',
  forex: 'Forex',
  stocks: 'Stocks',
  company_news: 'Company News',
  commodities: 'Commodities',
};

export const NEWS_LANGUAGES = [
  'en',
  'es',
  'de',
  'fr',
  'it',
  'pt',
  'ru',
  'ja',
  'zh',
  'ar',
  'bg',
  'cs',
  'fa',
  'he',
  'hu',
  'ms',
  'pl',
  'ro',
  'sk',
  'sv',
  'th',
  'uk',
] as const;

export type NewsLanguage = (typeof NEWS_LANGUAGES)[number];

export const LANGUAGE_LABELS: Record<NewsLanguage, string> = {
  en: 'English (EN)',
  es: 'Español (ES)',
  de: 'Deutsch (DE)',
  fr: 'Français (FR)',
  it: 'Italiano (IT)',
  pt: 'Português (PT)',
  ru: 'Русский (RU)',
  ja: '日本語 (JA)',
  zh: '中文 (ZH)',
  ar: 'العربية (AR)',
  bg: 'Български (BG)',
  cs: 'Čeština (CS)',
  fa: 'فارسی (FA)',
  he: 'עברית (HE)',
  hu: 'Magyar (HU)',
  ms: 'Bahasa Melayu (MS)',
  pl: 'Polski (PL)',
  ro: 'Română (RO)',
  sk: 'Slovenčina (SK)',
  sv: 'Svenska (SV)',
  th: 'ไทย (TH)',
  uk: 'Українська (UK)',
};

export interface NewsWidgetConfig {
  header: boolean;
  borders: boolean;
  defaultLanguage: NewsLanguage;
  availableLanguages: readonly NewsLanguage[];
  newsCategories: readonly NewsCategory[];
  width: string;
  height: string;
  adv: 'popup' | 'blank';
}

export interface NewsWidgetProps {
  className?: string;
  defaultCategories?: readonly NewsCategory[];
  defaultLanguage?: NewsLanguage;
  height?: string | number;
}
