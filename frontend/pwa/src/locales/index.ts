/**
 * Translations for PWA Worker App
 */

import en from './en';
import sr from './sr';

export type Language = 'en' | 'sr';

export const translations = {
  en,
  sr,
};

export const getTranslation = (language: Language = 'sr') => {
  return translations[language] || translations.sr;
};

export default translations;
