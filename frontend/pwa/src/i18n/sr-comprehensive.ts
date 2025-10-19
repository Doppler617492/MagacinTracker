/**
 * Serbian (Srpski) Language Constants - Comprehensive
 * Manhattan Active WMS Style - Enterprise WMS Terminology
 * 
 * Note: Using Latin script for better device compatibility
 * Can be converted to Cyrillic if needed
 */

export const sr = {
  // ========================================
  // NAVIGATION & MENU
  // ========================================
  navigation: {
    zadaci: "Zadaci",
    zadaciTima: "Zadaci tima",
    pretragaArtikla: "Pretraga artikla",
    popisMagacina: "Popis magacina",
    podesavanja: "Podešavanja",
    profil: "Profil",
    pocetna: "Početna",
    nazad: "Nazad",
    odjava: "Odjava"
  },

  // ========================================
  // HEADER & STATUS
  // ========================================
  header: {
    online: "Online",
    offline: "Offline",
    sinhronizacija: "Sinhronizacija...",
    smjena: "Smjena",
    pauza: "Pauza",
    tim: "Tim"
  },

  // ========================================
  // SHIFT & TEAM
  // ========================================
  shift: {
    smjenaA: "Smjena A",
    smjenaB: "Smjena B",
    vrijemeA: "08:00–15:00",
    vrijemeB: "12:00–19:00",
    pauzaA: "10:00–10:30",
    pauzaB: "14:00–14:30",
    aktivnaSmjena: "Aktivna smjena",
    preostaloVrijeme: "Preostalo vrijeme"
  },

  team: {
    tim: "Tim",
    clanTima: "Član tima",
    partner: "Partner",
    timA1: "Tim A1",
    timB1: "Tim B1",
    samoMoji: "Samo moji",
    timskiZadaci: "Timski zadaci",
    partneri: "Partneri",
    partnerOnline: "Partner online",
    partnerOffline: "Partner offline"
  },

  // ========================================
  // TASKS & DOCUMENTS
  // ========================================
  task: {
    zadatak: "Zadatak",
    zadaci: "Zadaci",
    dokumentBroj: "Dokument broj",
    datum: "Datum",
    status: "Status",
    prioritet: "Prioritet",
    radnja: "Radnja",
    magacin: "Magacin",
    
    // Quantities
    trazeno: "Traženo",
    pronadjeno: "Pronađeno",
    preostalo: "Preostalo",
    ukupno: "Ukupno",
    kolicina: "Količina",
    jedinicaMjere: "Jedinica mjere",
    
    // Status values
    nov: "Nov",
    dodijeljen: "Dodijeljen",
    uToku: "U toku",
    zavrsen: "Završen",
    zavrsenoDjelimicno: "Završeno (djelimično)",
    neuspjesno: "Neuspješno",
    
    // Priority
    niski: "Niski",
    normalan: "Normalan",
    visoki: "Visoki",
    
    // Actions
    zapocni: "Započni",
    nastavi: "Nastavi",
    pauziraj: "Pauziraj",
    zavrsi: "Završi",
    dovrsiZadatak: "Dovrši zadatak",
    odustani: "Odustani",
    potvrdi: "Potvrdi",
    
    // Progress
    napredak: "Napredak",
    procenatIspunjenja: "% ispunjenja",
    zavrseno: "Završeno",
    stavke: "Stavke",
    stavkeZavrseno: "stavke završeno"
  },

  // ========================================
  // PARTIAL COMPLETION & REASONS
  // ========================================
  partial: {
    djelimicnoZavrsen: "Djelimično završen",
    markirajPreostalo: "Markiraj preostalo = 0",
    odaberiRazlog: "Odaberi razlog",
    razlog: "Razlog",
    razlozi: "Razlozi",
    unesite: "Unesite",
    
    // Reasons enum
    nemaNaStanju: "Nema na stanju",
    osteceno: "Oštećeno",
    nijePronađeno: "Nije pronađeno",
    krivi_artikal: "Krivi artikal",
    drugo: "Drugo",
    drugoUnesite: "Drugo (unesite)",
    
    // Messages
    manjaKolicina: "Manja količina od tražene",
    obrazlozite: "Molimo obrazložite",
    obaveznoPolje: "Obavezno polje ako je količina manja"
  },

  // ========================================
  // CATALOG & ARTICLES
  // ========================================
  catalog: {
    artikal: "Artikal",
    artikli: "Artikli",
    sifra: "Šifra",
    naziv: "Naziv",
    barkod: "Barkod",
    pretraga: "Pretraga",
    pretraziPoSifri: "Pretraži po šifri",
    pretraziPoNazivu: "Pretraži po nazivu",
    pretraziPoBarkodu: "Pretraži po barkodu",
    
    // Barcode
    skenirajBarkod: "Skeniraj barkod",
    unesiBarkod: "Unesi barkod",
    potrebanBarkod: "Potreban barkod",
    nemaBarkoda: "Nema barkoda",
    
    // Results
    rezultati: "Rezultati",
    pronađeno: "Pronađeno",
    nisuPronađeniRezultati: "Nisu pronađeni rezultati",
    pretražite: "Pretražite artikle"
  },

  // ========================================
  // INVENTORY COUNT (Popis)
  // ========================================
  count: {
    popis: "Popis",
    popisMagacina: "Popis magacina",
    novoPrebrojavanje: "Novo prebrojavanje",
    lokacija: "Lokacija",
    prebrojanaKolicina: "Prebrojana količina",
    sistemskaKolicina: "Sistemska količina",
    razlika: "Razlika",
    sacuvaj: "Sačuvaj",
    spremiPrebrojavanje: "Spremi prebrojavanje",
    potvrdaPopisa: "Potvrda popisa"
  },

  // ========================================
  // SCANNING
  // ========================================
  scan: {
    skeniranje: "Skeniranje",
    skeniraj: "Skeniraj",
    skeniranjeBarkoda: "Skeniranje barkoda",
    uspjesnoSkenirano: "Uspješno skenirano",
    nevalidanBarkod: "Nevalidan barkod",
    barkodNijePronađen: "Barkod nije pronađen",
    pokusajPonovo: "Pokušaj ponovo"
  },

  // ========================================
  // USER & PROFILE
  // ========================================
  user: {
    ime: "Ime",
    prezime: "Prezime",
    punoIme: "Puno ime",
    korisnickoIme: "Korisničko ime",
    email: "Email",
    lozinka: "Lozinka",
    uloga: "Uloga",
    
    // Roles
    admin: "Administrator",
    menadzer: "Menadžer",
    sef: "Šef",
    komercijalista: "Komercijalista",
    magacioner: "Magacioner",
    
    // Profile
    profil: "Profil",
    mojProfil: "Moj profil",
    promjeniLozinku: "Promijeni lozinku",
    podesavanjaProfila: "Podešavanja profila"
  },

  // ========================================
  // SETTINGS
  // ========================================
  settings: {
    podesavanja: "Podešavanja",
    jezik: "Jezik",
    tema: "Tema",
    obavjestenja: "Obavještenja",
    zvuk: "Zvuk",
    vibracije: "Vibracije",
    
    // Offline
    offlineRezim: "Offline režim",
    sinhronizuj: "Sinhronizuj",
    automatskaSinhronizacija: "Automatska sinhronizacija",
    cekajuNaSinhronizaciju: "Čekaju na sinhronizaciju",
    zadnjaAzurnost: "Zadnja ažurnost",
    
    // App info
    verzija: "Verzija",
    informacije: "Informacije",
    oAplikaciji: "O aplikaciji",
    pomoc: "Pomoć",
    podrska: "Podrška"
  },

  // ========================================
  // MESSAGES & FEEDBACK
  // ========================================
  messages: {
    uspjeh: "Uspjeh",
    greska: "Greška",
    upozorenje: "Upozorenje",
    informacija: "Informacija",
    
    // Success messages
    uspjesnoSacuvano: "Uspješno sačuvano",
    uspjesnoAzurirano: "Uspješno ažurirano",
    uspjesnoObrisano: "Uspješno obrisano",
    zadatakZavrsen: "Zadatak završen",
    dokumentZavrsen: "Dokument završen",
    
    // Error messages
    greskaUcitavanja: "Greška učitavanja",
    greskaCuvanja: "Greška čuvanja",
    pokusajPonovo: "Pokušaj ponovo",
    nemaInternet: "Nema internet konekcije",
    neuspjesnaAutentifikacija: "Neuspješna autentifikacija",
    
    // Validation
    obaveznoPolje: "Obavezno polje",
    nevalidanFormat: "Nevalidan format",
    nevalidnaKolicina: "Nevalidna količina",
    kolicinaVecaOdTrazene: "Količina veća od tražene",
    kolicinaManjaOdNule: "Količina ne može biti manja od 0",
    
    // Confirmations
    daLiSteSigurni: "Da li ste sigurni?",
    potvrdiAkciju: "Potvrdi akciju",
    nelzePovratiti: "Ova akcija se ne može povratiti",
    da: "Da",
    ne: "Ne",
    odustani: "Odustani"
  },

  // ========================================
  // DATES & TIMES
  // ========================================
  datetime: {
    danas: "Danas",
    juce: "Juče",
    sutra: "Sutra",
    ova_sedmica: "Ova sedmica",
    prosla_sedmica: "Prošla sedmica",
    ovaj_mjesec: "Ovaj mjesec",
    prosli_mjesec: "Prošli mjesec",
    
    // Days
    ponedeljak: "Ponedjeljak",
    utorak: "Utorak",
    srijeda: "Srijeda",
    cetvrtak: "Četvrtak",
    petak: "Petak",
    subota: "Subota",
    nedjelja: "Nedjelja",
    
    // Months
    januar: "Januar",
    februar: "Februar",
    mart: "Mart",
    april: "April",
    maj: "Maj",
    juni: "Juni",
    juli: "Juli",
    avgust: "Avgust",
    septembar: "Septembar",
    oktobar: "Oktobar",
    novembar: "Novembar",
    decembar: "Decembar",
    
    // Time
    sati: "sati",
    minuta: "minuta",
    sekundi: "sekundi",
    prije: "prije",
    poslije: "poslije"
  },

  // ========================================
  // ACTIONS & BUTTONS
  // ========================================
  actions: {
    dodaj: "Dodaj",
    sacuvaj: "Sačuvaj",
    azuriraj: "Ažuriraj",
    obrisi: "Obriši",
    otkazi: "Otkaži",
    potvrdi: "Potvrdi",
    zatvori: "Zatvori",
    pretrazi: "Pretraži",
    filtriraj: "Filtriraj",
    resetuj: "Resetuj",
    osvjezi: "Osvježi",
    ucitaj: "Učitaj",
    preuzmi: "Preuzmi",
    izvezi: "Izvezi",
    stampaj: "Štampaj",
    detalji: "Detalji",
    uredi: "Uredi",
    pregledaj: "Pregledaj",
    povratak: "Povratak"
  },

  // ========================================
  // STATES & STATUSES
  // ========================================
  states: {
    ucitavanje: "Učitavanje...",
    cuvanje: "Čuvanje...",
    obrada: "Obrada...",
    sinhronizacija: "Sinhronizacija...",
    zavrseno: "Završeno",
    uspjeh: "Uspjeh",
    neuspjeh: "Neuspjeh",
    aktivno: "Aktivno",
    neaktivno: "Neaktivno",
    dostupno: "Dostupno",
    nedostupno: "Nedostupno"
  },

  // ========================================
  // FILTERS & SORTING
  // ========================================
  filters: {
    filtriraj: "Filtriraj",
    sortiraj: "Sortiraj",
    svi: "Svi",
    aktivni: "Aktivni",
    neaktivni: "Neaktivni",
    datumOd: "Datum od",
    datumDo: "Datum do",
    rastuće: "Rastuće",
    opadajuće: "Opadajuće",
    primijeni: "Primijeni",
    ocisti: "Očisti"
  },

  // ========================================
  // PAGINATION
  // ========================================
  pagination: {
    stranica: "Stranica",
    od: "od",
    ukupno: "Ukupno",
    prikaziPoStranici: "Prikaži po stranici",
    sljedeca: "Sljedeća",
    prethodna: "Prethodna",
    prva: "Prva",
    zadnja: "Zadnja"
  },

  // ========================================
  // EMPTY STATES
  // ========================================
  empty: {
    nemaZadataka: "Nema zadataka",
    nemaRezultata: "Nema rezultata",
    nemaPodataka: "Nema podataka",
    nistaZaPrikazati: "Nema ništa za prikazati",
    pocetak: "Započnite pretraživanjem ili dodavanjem novog"
  },

  // ========================================
  // LOGIN & AUTHENTICATION
  // ========================================
  auth: {
    prijava: "Prijava",
    odjava: "Odjava",
    korisnickoIme: "Korisničko ime",
    lozinka: "Lozinka",
    zapamtiMe: "Zapamti me",
    zaboravilLozinku: "Zaboravili ste lozinku?",
    prijavite_se: "Prijavite se",
    nevalidniPodaci: "Nevalidni podaci za prijavu",
    sesijаIstekla: "Sesija je istekla. Prijavite se ponovo."
  },

  // ========================================
  // NOTIFICATIONS
  // ========================================
  notifications: {
    obavjestenja: "Obavještenja",
    novZadatak: "Nov zadatak",
    azuriranZadatak: "Ažuriran zadatak",
    zavrsenZadatak: "Završen zadatak",
    novDokument: "Nov dokument",
    partnerAzurirao: "Partner je ažurirao zadatak",
    timAzurirao: "Tim je ažurirao zadatak",
    sinhronizovano: "Podaci sinhronizovani",
    offlineRezim: "Offline režim aktiviran"
  },

  // ========================================
  // ERRORS
  // ========================================
  errors: {
    opstaGreska: "Došlo je do greške",
    mreznaGreska: "Greška mreže",
    serverGreska: "Greška servera",
    greskaBazePodataka: "Greška baze podataka",
    neovlasteniPristup: "Neovlašteni pristup",
    nijePronadjeno: "Nije pronađeno",
    greska404: "Stranica nije pronađena",
    greska500: "Interna greška servera",
    kontaktirajPodrsku: "Molimo kontaktirajte podršku"
  },

  // ========================================
  // HELP & SUPPORT
  // ========================================
  help: {
    pomoc: "Pomoć",
    uputstva: "Uputstva",
    cesta_pitanja: "Česta pitanja",
    kontakt: "Kontakt",
    podrska: "Podrška",
    prijavi_problem: "Prijavi problem",
    dokumentacija: "Dokumentacija"
  }
};

// ========================================
// HELPER FUNCTIONS
// ========================================

/**
 * Format number for Serbian locale
 */
export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('sr-RS').format(num);
};

/**
 * Format date for Serbian locale
 */
export const formatDate = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('sr-RS', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(d);
};

/**
 * Format datetime for Serbian locale
 */
export const formatDateTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('sr-RS', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(d);
};

/**
 * Format time for Serbian locale
 */
export const formatTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('sr-RS', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(d);
};

/**
 * Get relative time in Serbian
 */
export const getRelativeTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Upravo sad';
  if (diffMins < 60) return `prije ${diffMins} ${diffMins === 1 ? 'minut' : 'minuta'}`;
  if (diffHours < 24) return `prije ${diffHours} ${diffHours === 1 ? 'sat' : 'sati'}`;
  if (diffDays === 1) return 'Juče';
  if (diffDays < 7) return `prije ${diffDays} dana`;
  
  return formatDate(d);
};

/**
 * Get shift label
 */
export const getShiftLabel = (shift: 'A' | 'B'): string => {
  return shift === 'A' ? sr.shift.smjenaA : sr.shift.smjenaB;
};

/**
 * Get shift time
 */
export const getShiftTime = (shift: 'A' | 'B'): string => {
  return shift === 'A' ? sr.shift.vrijemeA : sr.shift.vrijemeB;
};

/**
 * Get shift pause
 */
export const getShiftPause = (shift: 'A' | 'B'): string => {
  return shift === 'A' ? sr.shift.pauzaA : sr.shift.pauzaB;
};

export default sr;

