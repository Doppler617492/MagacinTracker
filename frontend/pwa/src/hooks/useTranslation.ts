/**
 * Translation hook for PWA Worker App
 */

import { useMemo } from 'react';
import { getTranslation, Language } from '../locales/index';

export const useTranslation = (language: Language = 'sr') => {
  return useMemo(() => {
    return getTranslation(language);
  }, [language]);
};

export default useTranslation;
