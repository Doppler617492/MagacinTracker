// Internationalization support for English and Serbian
export type Language = 'en' | 'sr';

export const translations = {
  en: {
    // Home Screen
    home: {
      myTasks: 'My Tasks',
      teamTasks: 'Team Tasks',
      scanPick: 'Scan & Pick',
      manualEntry: 'Manual Entry',
      exceptions: 'Exceptions',
      stockCount: 'Stock Count',
      lookup: 'Lookup',
      history: 'History',
      settings: 'Settings',
    },
    // Header
    header: {
      online: 'Online',
      offline: 'Offline',
      synced: 'Synced',
      pending: 'Pending',
      shift: 'Shift',
      break: 'Break',
      toBreak: 'to break',
      toEnd: 'to end of break',
      battery: 'Battery',
    },
    // Tasks
    tasks: {
      all: 'All',
      active: 'Active',
      inProgress: 'In Progress',
      new: 'New',
      partial: 'Partial',
      completed: 'Completed',
      finishTask: 'Finish Task',
      saveExit: 'Save & Exit',
      enterQuantity: 'Enter Quantity',
      closeItem: 'Close Item',
      reason: 'Reason',
      note: 'Note',
      required: 'Required',
      optional: 'Optional',
    },
    // Stock Count
    stockCount: {
      title: 'Stock Count',
      adHoc: 'Ad-hoc Count',
      guided: 'Guided Count',
      scanLocation: 'Scan Location',
      enterLocation: 'Enter Location',
      scanSKU: 'Scan SKU',
      enterSKU: 'Enter SKU',
      counted: 'Counted',
      systemQty: 'System Qty',
      variance: 'Variance',
      submit: 'Submit Count',
      history: 'Count History',
    },
    // Reasons
    reasons: {
      outOfStock: 'Out of stock',
      notFound: 'Not found',
      damaged: 'Damaged',
      wrongDocument: 'Wrong document entry',
      other: 'Other',
      missing: 'Missing',
      misplaced: 'Misplaced',
    },
    // Common
    common: {
      confirm: 'Confirm',
      cancel: 'Cancel',
      save: 'Save',
      delete: 'Delete',
      edit: 'Edit',
      search: 'Search',
      filter: 'Filter',
      loading: 'Loading...',
      noData: 'No data',
      error: 'Error',
      success: 'Success',
    },
  },
  sr: {
    // Home Screen
    home: {
      myTasks: 'Moji zadaci',
      teamTasks: 'Zadaci tima',
      scanPick: 'Sken i pokupi',
      manualEntry: 'Ručni unos',
      exceptions: 'Izuzeci',
      stockCount: 'Popis',
      lookup: 'Pretraga',
      history: 'Istorija',
      settings: 'Podešavanja',
    },
    // Header
    header: {
      online: 'Online',
      offline: 'Offline',
      synced: 'Sinhronizovano',
      pending: 'Na čekanju',
      shift: 'Smjena',
      break: 'Pauza',
      toBreak: 'do pauze',
      toEnd: 'do kraja pauze',
      battery: 'Baterija',
    },
    // Tasks
    tasks: {
      all: 'Sve',
      active: 'Aktivne',
      inProgress: 'U toku',
      new: 'Nove',
      partial: 'Djelimične',
      completed: 'Završene',
      finishTask: 'Završi zadatak',
      saveExit: 'Sačuvaj i izađi',
      enterQuantity: 'Unesi količinu',
      closeItem: 'Zatvori stavku',
      reason: 'Razlog',
      note: 'Napomena',
      required: 'Obavezno',
      optional: 'Opciono',
    },
    // Stock Count
    stockCount: {
      title: 'Popis',
      adHoc: 'Brzi popis',
      guided: 'Vođeni popis',
      scanLocation: 'Skeniraj lokaciju',
      enterLocation: 'Unesi lokaciju',
      scanSKU: 'Skeniraj šifru',
      enterSKU: 'Unesi šifru',
      counted: 'Izbrojano',
      systemQty: 'Sistemska kol.',
      variance: 'Razlika',
      submit: 'Pošalji popis',
      history: 'Istorija popisa',
    },
    // Reasons
    reasons: {
      outOfStock: 'Nije na stanju',
      notFound: 'Nije pronađeno',
      damaged: 'Oštećeno',
      wrongDocument: 'Pogrešan navod u dokumentu',
      other: 'Drugo',
      missing: 'Nedostaje',
      misplaced: 'Premješteno',
    },
    // Common
    common: {
      confirm: 'Potvrdi',
      cancel: 'Odustani',
      save: 'Sačuvaj',
      delete: 'Obriši',
      edit: 'Izmijeni',
      search: 'Pretraži',
      filter: 'Filter',
      loading: 'Učitavanje...',
      noData: 'Nema podataka',
      error: 'Greška',
      success: 'Uspjeh',
    },
  },
};

// Get current language from localStorage or default to Serbian
export const getCurrentLanguage = (): Language => {
  const stored = localStorage.getItem('language');
  return (stored === 'en' || stored === 'sr') ? stored : 'sr';
};

// Set language
export const setLanguage = (lang: Language) => {
  localStorage.setItem('language', lang);
  window.location.reload(); // Reload to apply changes
};

// Get translation helper
export const t = (path: string): string => {
  const lang = getCurrentLanguage();
  const keys = path.split('.');
  let value: any = translations[lang];
  
  for (const key of keys) {
    value = value?.[key];
    if (value === undefined) break;
  }
  
  return value ?? path;
};

