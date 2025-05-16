import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, forkJoin, BehaviorSubject } from 'rxjs';
import { catchError, tap, map } from 'rxjs/operators';
import { environment } from '../../src/environments/environment';




export interface MapInfo {
  center: {
    lat: number;
    lng: number;
  };
  zoom: number;
  regions: {
    name: string;
    code: string;
    voters: number;
    percentage: number;
  }[];
}

export interface ElectionRoundState {
  roundId: string;
  hasData: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class MapService {
  // URL-ul API
  private apiUrl = environment.apiUrl;
  
  
  // Path for GeoJSON and CSV
  private geoJsonPath = 'assets/maps/romania.geojson';
  private csvPath = 'assets/data/presence_2024-12-06.csv';
  private currentRoundState = new BehaviorSubject<ElectionRoundState>({
  roundId: 'tur1_2024', // Implicit Tur 1 2024
  hasData: true // Implicit are date
});


// Observable pentru ascultarea schimbărilor de tur
public currentRound$ = this.currentRoundState.asObservable();
setCurrentRound(roundId: string, hasData: boolean): void {
  console.log(`MapService: Setare tur curent - ${roundId}, are date: ${hasData}`);
  this.currentRoundState.next({ roundId, hasData });
}

/**
 * Obține starea curentă a turului
 */
getCurrentRound(): ElectionRoundState {
  return this.currentRoundState.getValue();
}
/**
 * Returnează date goale pentru hartă (fără votanți)
 */
private getEmptyMapData(): Observable<MapInfo> {
  // Creăm date goale pentru județe
  const emptyData: MapInfo = {
    center: { lat: 45.9443, lng: 25.0094 },
    zoom: 7,
    regions: [
      { name: 'București', code: 'B', voters: 0, percentage: 0 },
      { name: 'Cluj', code: 'CJ', voters: 0, percentage: 0 },
      // Adaugă toate județele cu valori 0
      // ...restul județelor
      { name: 'Vrancea', code: 'VN', voters: 0, percentage: 0 }
    ]
  };

  return of(emptyData);
}
/**
 * Returnează date goale pentru harta mondială (fără votanți)
 */
private getEmptyWorldVotingData(): any {
  // Creează o copie a datelor reale dar cu valori zero
  const realData = this.getRealWorldData();
  const emptyData: any = {};

  Object.keys(realData).forEach(countryCode => {
    const country = { ...realData[countryCode] };
    // Setăm toate datele numerice la 0, păstrând celelalte proprietăți
    country.voters = 0;
    country.percentage = 0;
    country.permanentListVoters = 0;
    country.correspondenceVoters = 0;
    country.totalVoters = 0;
    // Păstrăm numărul de secții de votare pentru a afișa corect harta
    emptyData[countryCode] = country;
  });

  return emptyData;
}

/**
 * Returnează datele reale mondiale (metoda auxiliară)
 */
private getRealWorldData(): any {
  return {
    'USA': { 
      name: 'United States', 
      code: 'USA', 
      voters: 15000, 
      percentage: 0.45, 
      pollingStationCount: 71,
      permanentListVoters: 12500,
      correspondenceVoters: 2500,
      totalVoters: 15000
    },
    // ...și restul țărilor
  };
}


  // Cache pentru datele GeoJSON UAT
  private uatGeoJsonCache: { [countyCode: string]: any } = {};

  constructor(private http: HttpClient) { }

  /**
   * Fetches map information from the API
   */
  getMapInfo(): Observable<MapInfo> {
    console.log('Serviciu: Încercare de a obține date hartă');
    // Obține starea curentă a turului
    const currentRound = this.getCurrentRound();

    if (!currentRound.hasData) {
      console.log('Tur fără date preîncărcate - se returnează hartă goală');
      return this.getEmptyMapData();
    }
    
    // URL-ul către endpoint-ul pentru hartă
    const url = `${this.apiUrl}menu/map/`;
    console.log('URL API apelat:', url);
    
    return this.http.get<MapInfo>(url).pipe(
      tap(data => console.log('Date primite de la API:', data)),
      catchError(error => {
        console.error('Eroare la obținerea datelor hartă:', error);
        
        // În caz de eroare, returnează date fictive pentru testare
        const mockData: MapInfo = {
          center: { lat: 45.9443, lng: 25.0094 },
          zoom: 7,
          regions: [
            { name: 'București', code: 'B', voters: 12500, percentage: 0.65 },
            { name: 'Cluj', code: 'CJ', voters: 8300, percentage: 0.42 },
            { name: 'Iași', code: 'IS', voters: 7600, percentage: 0.38 },
            { name: 'Alba', code: 'AB', voters: 3200, percentage: 0.16 },
            { name: 'Arad', code: 'AR', voters: 4100, percentage: 0.20 },
            { name: 'Argeș', code: 'AG', voters: 5300, percentage: 0.26 },
            { name: 'Bacău', code: 'BC', voters: 4800, percentage: 0.24 },
            { name: 'Bihor', code: 'BH', voters: 5100, percentage: 0.25 },
            { name: 'Bistrița-Năsăud', code: 'BN', voters: 2600, percentage: 0.13 },
            { name: 'Botoșani', code: 'BT', voters: 3400, percentage: 0.17 },
            { name: 'Brașov', code: 'BV', voters: 6200, percentage: 0.31 },
            { name: 'Brăila', code: 'BR', voters: 2900, percentage: 0.14 },
            { name: 'Buzău', code: 'BZ', voters: 3500, percentage: 0.17 },
            { name: 'Caraș-Severin', code: 'CS', voters: 2400, percentage: 0.12 },
            { name: 'Călărași', code: 'CL', voters: 2300, percentage: 0.11 },
            { name: 'Constanța', code: 'CT', voters: 6500, percentage: 0.32 },
            { name: 'Covasna', code: 'CV', voters: 1800, percentage: 0.09 },
            { name: 'Dâmbovița', code: 'DB', voters: 4100, percentage: 0.20 },
            { name: 'Dolj', code: 'DJ', voters: 5600, percentage: 0.28 },
            { name: 'Galați', code: 'GL', voters: 4900, percentage: 0.24 },
            { name: 'Giurgiu', code: 'GR', voters: 2200, percentage: 0.11 },
            { name: 'Gorj', code: 'GJ', voters: 3100, percentage: 0.15 },
            { name: 'Harghita', code: 'HR', voters: 2700, percentage: 0.13 },
            { name: 'Hunedoara', code: 'HD', voters: 3900, percentage: 0.19 },
            { name: 'Ialomița', code: 'IL', voters: 2200, percentage: 0.11 },
            { name: 'Ilfov', code: 'IF', voters: 3800, percentage: 0.19 },
            { name: 'Maramureș', code: 'MM', voters: 4300, percentage: 0.21 },
            { name: 'Mehedinți', code: 'MH', voters: 2500, percentage: 0.12 },
            { name: 'Mureș', code: 'MS', voters: 4700, percentage: 0.23 },
            { name: 'Neamț', code: 'NT', voters: 4200, percentage: 0.21 },
            { name: 'Olt', code: 'OT', voters: 3800, percentage: 0.19 },
            { name: 'Prahova', code: 'PH', voters: 6800, percentage: 0.34 },
            { name: 'Satu Mare', code: 'SM', voters: 3100, percentage: 0.15 },
            { name: 'Sălaj', code: 'SJ', voters: 2100, percentage: 0.10 },
            { name: 'Sibiu', code: 'SB', voters: 3900, percentage: 0.19 },
            { name: 'Suceava', code: 'SV', voters: 5700, percentage: 0.28 },
            { name: 'Teleorman', code: 'TR', voters: 3200, percentage: 0.16 },
            { name: 'Timiș', code: 'TM', voters: 6400, percentage: 0.32 },
            { name: 'Tulcea', code: 'TL', voters: 2100, percentage: 0.10 },
            { name: 'Vaslui', code: 'VS', voters: 3600, percentage: 0.18 },
            { name: 'Vâlcea', code: 'VL', voters: 3500, percentage: 0.17 },
            { name: 'Vrancea', code: 'VN', voters: 3000, percentage: 0.15 }
          ]
        };
        
        return of(mockData);
      })
    );
  }

    /**
   * Get UAT GeoJSON for a specific county
   */
    getCountyUATGeoJson(countyCode: string): Observable<any> {
      // Folosește codul județului cu MAJUSCULE pentru a se potrivi cu denumirile fișierelor
      // Obține starea curentă a turului
      const currentRound = this.getCurrentRound();
      if (!currentRound.hasData) {
        console.log('Tur fără date UAT preîncărcate - se returnează date goale');
        return of(null);
     }
      
      const upperCaseCode = countyCode.toUpperCase();
      
      // Verifică dacă datele sunt deja în cache
      if (this.uatGeoJsonCache[upperCaseCode]) {
        console.log(`Folosește date din cache pentru județul ${countyCode}`);
        return of(this.uatGeoJsonCache[upperCaseCode]);
      }
      
      const uatGeoJsonUrl = `assets/maps/uat/${upperCaseCode}.geojson`;
      
      console.log(`Încercare încărcare GeoJSON UAT pentru județul ${countyCode} de la: ${uatGeoJsonUrl}`);
      
      return this.http.get(uatGeoJsonUrl).pipe(
        tap(data => {
          console.log(`GeoJSON UAT pentru județul ${countyCode} încărcat cu succes`);
          // Adaugă datele în cache
          this.uatGeoJsonCache[upperCaseCode] = data;
        }),
        catchError(error => {
          console.error(`Eroare la încărcarea GeoJSON UAT pentru județul ${countyCode}:`, error);
          return of(null);
        })
      );
    }
  
    preloadAllUATGeoJson(): Observable<any> {
      const countyCodes = [
        'AB', 'AR', 'AG', 'BC', 'BH', 'BN', 'BT', 'BV', 'BR', 'B', 'BZ', 'CS', 
        'CL', 'CJ', 'CT', 'CV', 'DB', 'DJ', 'GL', 'GR', 'GJ', 'HR', 'HD', 'IL', 
        'IS', 'IF', 'MM', 'MH', 'MS', 'NT', 'OT', 'PH', 'SM', 'SJ', 'SB', 'SV', 
        'TR', 'TM', 'TL', 'VS', 'VL', 'VN'
      ];
      
      const observables = countyCodes.map(code => 
        this.getCountyUATGeoJson(code)
      );
      
      return forkJoin(observables);
    }
  
  /**
   * Fetches and processes voting statistics from CSV file
   */
/**
 * Fetches and processes voting statistics from CSV file
 */
getVotingStatistics(): Observable<any> {
  console.log('Încercare încărcare CSV de la:', this.csvPath);

    // Obține starea curentă a turului
  const currentRound = this.getCurrentRound();
    if (!currentRound.hasData) {
    console.log('Tur fără date CSV preîncărcate - se returnează date goale');
    return of({});
  }
  
  // Încercăm să încărcăm fișierul CSV
  return this.http.get(this.csvPath, { responseType: 'text' }).pipe(
    tap(csvData => {
      console.log('CSV încărcat cu succes, lungime:', csvData.length);
      console.log('Primele 200 caractere:', csvData.substring(0, 200).replace(/\n/g, '\\n').replace(/\t/g, '\\t'));
    }),
    map(csvData => {
      // Detecție codare (BOM)
      if (csvData.charCodeAt(0) === 0xFEFF) {
        console.log('BOM detectat, se elimină');
        csvData = csvData.slice(1);
      }
      return this.processVotingData(csvData);
    }),
    tap(result => {
      console.log('Rezultat procesare CSV:', Object.keys(result).length, 'județe');
      if (Object.keys(result).length === 0) {
        console.error('Nu s-au găsit date în CSV! Se utilizează date implicite.');
      }
    }),
    map(result => {
      // Dacă nu s-au găsit date în CSV, utilizăm date implicite
      if (Object.keys(result).length === 0) {
        return this.getDefaultVotingData();
      }
      return result;
    }),
    catchError(error => {
      console.error('Error loading CSV data:', error);
      console.log('Se încarcă datele implicite...');
      return of(this.getDefaultVotingData());
    })
  );
}
  
  /**
   * Process voting data from tab-separated CSV file
   */
  private processVotingData(csvData: string): any {
    console.log('Processing CSV data...');
    
    // Split by lines and filter out empty ones
    const lines = csvData.split('\n').filter(line => line.trim() !== '');
    
    if (lines.length === 0) {
      console.error('CSV is empty');
      return this.getDefaultVotingData();
    }
    
    // Parse the header row
    const headers = lines[0].split('\t');
    console.log('CSV Headers:', headers);
    
    // Find column indices - make sure to handle exact column name matches
    const countyIndex = headers.findIndex(h => h.trim() === 'Judet');
    const pollingStationNumberIndex = headers.findIndex(h => h.trim() === 'Nr sectie de votare');
    const registeredVotersIndex = headers.findIndex(h => h.trim() === 'Înscriși pe liste permanente');
    const permanentListVotersIndex = headers.findIndex(h => h.trim() === 'LP');
    const supplementaryListVotersIndex = headers.findIndex(h => h.trim() === 'LS');
    const specialCircumstancesVotersIndex = headers.findIndex(h => h.trim() === 'LSC');
    const mobileUrnsVotersIndex = headers.findIndex(h => h.trim() === 'UM');
    
    console.log('Column indices:', {
      countyIndex,
      pollingStationNumberIndex,
      registeredVotersIndex,
      permanentListVotersIndex,
      supplementaryListVotersIndex,
      specialCircumstancesVotersIndex,
      mobileUrnsVotersIndex
    });
    
    // If essential columns are missing, use hardcoded values for testing
    if (countyIndex === -1 || registeredVotersIndex === -1) {
      console.error('Essential columns missing in CSV, using default indices');
      // Try using hardcoded indices based on known column positions
      return this.processVotingDataWithHardcodedIndices(lines);
    }
    
    // Initialize county data
    const countyData: { [key: string]: any } = {};
    
    // Skip header row
    for (let i = 1; i < lines.length; i++) {
      const cells = lines[i].split('\t');
      
      if (cells.length <= Math.max(countyIndex, registeredVotersIndex)) continue;
      
      const county = cells[countyIndex].trim();
      const pollingStationNumber = pollingStationNumberIndex !== -1 ? cells[pollingStationNumberIndex] : i.toString();
      const registeredVoters = parseInt(cells[registeredVotersIndex] || '0', 10);
      const permanentListVoters = permanentListVotersIndex !== -1 ? parseInt(cells[permanentListVotersIndex] || '0', 10) : 0;
      const supplementaryListVoters = supplementaryListVotersIndex !== -1 ? parseInt(cells[supplementaryListVotersIndex] || '0', 10) : 0;
      const specialCircumstancesVoters = specialCircumstancesVotersIndex !== -1 ? parseInt(cells[specialCircumstancesVotersIndex] || '0', 10) : 0;
      const mobileUrnsVoters = mobileUrnsVotersIndex !== -1 ? parseInt(cells[mobileUrnsVotersIndex] || '0', 10) : 0;
      
      // Skip invalid rows
      if (!county) continue;
      
      // Initialize county data if not exists
      if (!countyData[county]) {
        countyData[county] = {
          registeredVoters: 0,
          pollingStations: new Set(),
          permanentListVoters: 0,
          supplementaryListVoters: 0,
          specialCircumstancesVoters: 0,
          mobileUrnsVoters: 0
        };
      }
      
      // Add data
      countyData[county].registeredVoters += registeredVoters;
      countyData[county].pollingStations.add(pollingStationNumber);
      countyData[county].permanentListVoters += permanentListVoters;
      countyData[county].supplementaryListVoters += supplementaryListVoters;
      countyData[county].specialCircumstancesVoters += specialCircumstancesVoters;
      countyData[county].mobileUrnsVoters += mobileUrnsVoters;
    }
    
    // Convert Set to count and calculate totals
    Object.keys(countyData).forEach(county => {
      const data = countyData[county];
      data.pollingStationCount = data.pollingStations.size;
      delete data.pollingStations;
      
      // Calculate total voters
      data.totalVoters = data.permanentListVoters + 
                          data.supplementaryListVoters + 
                          data.specialCircumstancesVoters + 
                          data.mobileUrnsVoters;
      
      // Calculate turnout percentage
      data.turnoutPercentage = data.registeredVoters > 0 
        ? (data.totalVoters / data.registeredVoters * 100).toFixed(2)
        : '0.00';
    });
    
    console.log('Processed county data:', Object.keys(countyData));
    return countyData;
  }
  
  
  /**
   * Fallback method to process CSV data with hardcoded column indices
   * This is used if column headers cannot be matched automatically
   */
  private processVotingDataWithHardcodedIndices(lines: string[]): any {
    console.log('Using hardcoded indices for CSV processing');
    console.log('Sample line[1]:', lines.length > 1 ? lines[1].substring(0, 100) : 'No data');
    
    // Hardcoded column indices based on the CSV format
    const countyIndex = 0;           // Judet
    const pollingStationNumberIndex = 4;  // Nr sectie de votare
    const registeredVotersIndex = 7;  // Înscriși pe liste permanente
    const permanentListVotersIndex = 8;   // LP
    const supplementaryListVotersIndex = 9;  // LS
    const specialCircumstancesVotersIndex = 10; // LSC
    const mobileUrnsVotersIndex = 11;     // UM
    
    // Initialize county data
    const countyData: { [key: string]: any } = {};
    
    // Skip header row, process all other rows
    let processedRows = 0;
    for (let i = 1; i < lines.length; i++) {
      const cells = lines[i].split('\t');
      
      if (cells.length <= registeredVotersIndex) {
        console.log(`Skipping row ${i} with insufficient columns: ${cells.length}`);
        continue;
      }
      
      const county = cells[countyIndex].trim();
      // Skip invalid rows
      if (!county) {
        console.log(`Skipping row ${i} with empty county`);
        continue;
      }
      
      const pollingStationNumber = cells[pollingStationNumberIndex] || i.toString();
      const registeredVoters = parseInt(cells[registeredVotersIndex] || '0', 10);
      const permanentListVoters = cells[permanentListVotersIndex] ? parseInt(cells[permanentListVotersIndex], 10) : 0;
      const supplementaryListVoters = cells[supplementaryListVotersIndex] ? parseInt(cells[supplementaryListVotersIndex], 10) : 0;
      const specialCircumstancesVoters = cells[specialCircumstancesVotersIndex] ? parseInt(cells[specialCircumstancesVotersIndex], 10) : 0;
      const mobileUrnsVoters = cells[mobileUrnsVotersIndex] ? parseInt(cells[mobileUrnsVotersIndex], 10) : 0;
      
      // Initialize county data if not exists
      if (!countyData[county]) {
        countyData[county] = {
          registeredVoters: 0,
          pollingStations: new Set(),
          permanentListVoters: 0,
          supplementaryListVoters: 0,
          specialCircumstancesVoters: 0,
          mobileUrnsVoters: 0,
          lastPollingStationNumber: 0
        };
      }
      
      // Add data
      countyData[county].registeredVoters += registeredVoters;
      countyData[county].pollingStations.add(pollingStationNumber);
      countyData[county].permanentListVoters += permanentListVoters;
      countyData[county].supplementaryListVoters += supplementaryListVoters;
      countyData[county].specialCircumstancesVoters += specialCircumstancesVoters;
      countyData[county].mobileUrnsVoters += mobileUrnsVoters;
      
      // Keep track of the latest polling station number
      const pollingStationNum = parseInt(pollingStationNumber, 10);
      if (!isNaN(pollingStationNum) && pollingStationNum > countyData[county].lastPollingStationNumber) {
        countyData[county].lastPollingStationNumber = pollingStationNum;
      }
      
      processedRows++;
    }
    
    console.log(`Processed ${processedRows} rows, found ${Object.keys(countyData).length} counties`);
    
    // Convert Set to count and calculate totals
    Object.keys(countyData).forEach(county => {
      const data = countyData[county];
      // Use the polling stations count or the last polling station number, whichever is greater
      data.pollingStationCount = Math.max(data.pollingStations.size, data.lastPollingStationNumber);
      delete data.pollingStations;
      delete data.lastPollingStationNumber;
      
      // Calculate total voters
      data.totalVoters = data.permanentListVoters + 
                          data.supplementaryListVoters + 
                          data.specialCircumstancesVoters + 
                          data.mobileUrnsVoters;
      
      // Calculate turnout percentage
      data.turnoutPercentage = data.registeredVoters > 0 
        ? (data.totalVoters / data.registeredVoters * 100).toFixed(2)
        : '0.00';
    });
    
    console.log('Processed counties:', Object.keys(countyData));
    return countyData;
  }
  
  
  /**
   * Get default mock voting data
   */
  private getDefaultVotingData(): any {
    // Mock voting statistics for testing when CSV loading fails
    return {
      'AB': { 
        registeredVoters: 301254, 
        pollingStationCount: 439, 
        permanentListVoters: 135372, 
        supplementaryListVoters: 10857, 
        specialCircumstancesVoters: 534, 
        mobileUrnsVoters: 2143, 
        totalVoters: 148906, 
        turnoutPercentage: "49.43" 
      },
      'AR': { 
        registeredVoters: 372641, 
        pollingStationCount: 437, 
        permanentListVoters: 146372, 
        supplementaryListVoters: 12408, 
        specialCircumstancesVoters: 487, 
        mobileUrnsVoters: 2251, 
        totalVoters: 161518, 
        turnoutPercentage: "43.34" 
      },
      'AG': { 
        registeredVoters: 511368, 
        pollingStationCount: 520, 
        permanentListVoters: 224576, 
        supplementaryListVoters: 14853, 
        specialCircumstancesVoters: 712, 
        mobileUrnsVoters: 3478, 
        totalVoters: 243619, 
        turnoutPercentage: "47.64" 
      },
      'BC': { 
        registeredVoters: 583217, 
        pollingStationCount: 634, 
        permanentListVoters: 237841, 
        supplementaryListVoters: 16785, 
        specialCircumstancesVoters: 854, 
        mobileUrnsVoters: 3912, 
        totalVoters: 259392, 
        turnoutPercentage: "44.48" 
      },
      'BH': { 
        registeredVoters: 499754, 
        pollingStationCount: 652, 
        permanentListVoters: 203546, 
        supplementaryListVoters: 14287, 
        specialCircumstancesVoters: 645, 
        mobileUrnsVoters: 2884, 
        totalVoters: 221362, 
        turnoutPercentage: "44.29" 
      },
      'BN': { 
        registeredVoters: 244327, 
        pollingStationCount: 313, 
        permanentListVoters: 108756, 
        supplementaryListVoters: 7435, 
        specialCircumstancesVoters: 387, 
        mobileUrnsVoters: 1743, 
        totalVoters: 118321, 
        turnoutPercentage: "48.43" 
      },
      'BT': { 
        registeredVoters: 350872, 
        pollingStationCount: 422, 
        permanentListVoters: 140532, 
        supplementaryListVoters: 8764, 
        specialCircumstancesVoters: 465, 
        mobileUrnsVoters: 2376, 
        totalVoters: 152137, 
        turnoutPercentage: "43.36" 
      },
      'BV': { 
        registeredVoters: 512742, 
        pollingStationCount: 447, 
        permanentListVoters: 235468, 
        supplementaryListVoters: 18765, 
        specialCircumstancesVoters: 723, 
        mobileUrnsVoters: 2568, 
        totalVoters: 257524, 
        turnoutPercentage: "50.22" 
      },
      'BR': { 
        registeredVoters: 294250, 
        pollingStationCount: 281, 
        permanentListVoters: 117543, 
        supplementaryListVoters: 7896, 
        specialCircumstancesVoters: 427, 
        mobileUrnsVoters: 2043, 
        totalVoters: 127909, 
        turnoutPercentage: "43.47" 
      },
      'B': { 
        registeredVoters: 1794329, 
        pollingStationCount: 1274, 
        permanentListVoters: 852764, 
        supplementaryListVoters: 83457, 
        specialCircumstancesVoters: 2367, 
        mobileUrnsVoters: 4915, 
        totalVoters: 943503, 
        turnoutPercentage: "52.58" 
      },
      'BZ': { 
        registeredVoters: 380123, 
        pollingStationCount: 427, 
        permanentListVoters: 163472, 
        supplementaryListVoters: 10543, 
        specialCircumstancesVoters: 587, 
        mobileUrnsVoters: 2678, 
        totalVoters: 177280, 
        turnoutPercentage: "46.64" 
      },
      'CS': { 
        registeredVoters: 266235, 
        pollingStationCount: 365, 
        permanentListVoters: 105438, 
        supplementaryListVoters: 6578, 
        specialCircumstancesVoters: 342, 
        mobileUrnsVoters: 1854, 
        totalVoters: 114212, 
        turnoutPercentage: "42.90" 
      },
      'CL': { 
        registeredVoters: 266412, 
        pollingStationCount: 235, 
        permanentListVoters: 102567, 
        supplementaryListVoters: 6753, 
        specialCircumstancesVoters: 312, 
        mobileUrnsVoters: 1632, 
        totalVoters: 111264, 
        turnoutPercentage: "41.76" 
      },
      'CJ': { 
        registeredVoters: 630548, 
        pollingStationCount: 619, 
        permanentListVoters: 313542, 
        supplementaryListVoters: 23879, 
        specialCircumstancesVoters: 967, 
        mobileUrnsVoters: 3842, 
        totalVoters: 342230, 
        turnoutPercentage: "54.28" 
      },
      'CT': { 
        registeredVoters: 631429, 
        pollingStationCount: 556, 
        permanentListVoters: 268754, 
        supplementaryListVoters: 22459, 
        specialCircumstancesVoters: 1078, 
        mobileUrnsVoters: 3745, 
        totalVoters: 296036, 
        turnoutPercentage: "46.88" 
      },
      'CV': { 
        registeredVoters: 181579, 
        pollingStationCount: 214, 
        permanentListVoters: 86547, 
        supplementaryListVoters: 5431, 
        specialCircumstancesVoters: 276, 
        mobileUrnsVoters: 1143, 
        totalVoters: 93397, 
        turnoutPercentage: "51.44" 
      },
      'DB': { 
        registeredVoters: 423721, 
        pollingStationCount: 432, 
        permanentListVoters: 178546, 
        supplementaryListVoters: 11345, 
        specialCircumstancesVoters: 543, 
        mobileUrnsVoters: 2564, 
        totalVoters: 192998, 
        turnoutPercentage: "45.55" 
      },
      'DJ': { 
        registeredVoters: 562763, 
        pollingStationCount: 529, 
        permanentListVoters: 238564, 
        supplementaryListVoters: 14653, 
        specialCircumstancesVoters: 712, 
        mobileUrnsVoters: 3756, 
        totalVoters: 257685, 
        turnoutPercentage: "45.79" 
      },
      'GL': { 
        registeredVoters: 518289, 
        pollingStationCount: 436, 
        permanentListVoters: 210548, 
        supplementaryListVoters: 12876, 
        specialCircumstancesVoters: 639, 
        mobileUrnsVoters: 3145, 
        totalVoters: 227208, 
        turnoutPercentage: "43.84" 
      },
      'GR': { 
        registeredVoters: 230742, 
        pollingStationCount: 245, 
        permanentListVoters: 95432, 
        supplementaryListVoters: 5678, 
        specialCircumstancesVoters: 312, 
        mobileUrnsVoters: 1532, 
        totalVoters: 102954, 
        turnoutPercentage: "44.62" 
      },
      'GJ': { 
        registeredVoters: 301529, 
        pollingStationCount: 332, 
        permanentListVoters: 138547, 
        supplementaryListVoters: 8432, 
        specialCircumstancesVoters: 423, 
        mobileUrnsVoters: 2156, 
        totalVoters: 149558, 
        turnoutPercentage: "49.60" 
      },
      'HR': { 
        registeredVoters: 267982, 
        pollingStationCount: 290, 
        permanentListVoters: 123457, 
        supplementaryListVoters: 6745, 
        specialCircumstancesVoters: 315, 
        mobileUrnsVoters: 1432, 
        totalVoters: 131949, 
        turnoutPercentage: "49.24" 
      },
      'HD': { 
        registeredVoters: 379254, 
        pollingStationCount: 524, 
        permanentListVoters: 162543, 
        supplementaryListVoters: 11354, 
        specialCircumstancesVoters: 587, 
        mobileUrnsVoters: 2643, 
        totalVoters: 177127, 
        turnoutPercentage: "46.70" 
      },
      'IL': { 
        registeredVoters: 245327, 
        pollingStationCount: 220, 
        permanentListVoters: 98765, 
        supplementaryListVoters: 5874, 
        specialCircumstancesVoters: 287, 
        mobileUrnsVoters: 1435, 
        totalVoters: 106361, 
        turnoutPercentage: "43.35" 
      },
      'IS': { 
        registeredVoters: 730541, 
        pollingStationCount: 755, 
        permanentListVoters: 329876, 
        supplementaryListVoters: 24567, 
        specialCircumstancesVoters: 1076, 
        mobileUrnsVoters: 4923, 
        totalVoters: 360442, 
        turnoutPercentage: "49.34" 
      },
      'IF': { 
        registeredVoters: 389764, 
        pollingStationCount: 255, 
        permanentListVoters: 198765, 
        supplementaryListVoters: 18965, 
        specialCircumstancesVoters: 512, 
        mobileUrnsVoters: 2134, 
        totalVoters: 220376, 
        turnoutPercentage: "56.54" 
      },
      'MM': { 
        registeredVoters: 418965, 
        pollingStationCount: 435, 
        permanentListVoters: 179865, 
        supplementaryListVoters: 12543, 
        specialCircumstancesVoters: 589, 
        mobileUrnsVoters: 2876, 
        totalVoters: 195873, 
        turnoutPercentage: "46.75" 
      },
      'MH': { 
        registeredVoters: 242358, 
        pollingStationCount: 286, 
        permanentListVoters: 101234, 
        supplementaryListVoters: 6543, 
        specialCircumstancesVoters: 312, 
        mobileUrnsVoters: 1765, 
        totalVoters: 109854, 
        turnoutPercentage: "45.33" 
      },
      'MS': { 
        registeredVoters: 476541, 
        pollingStationCount: 568, 
        permanentListVoters: 221456, 
        supplementaryListVoters: 14765, 
        specialCircumstancesVoters: 687, 
        mobileUrnsVoters: 3124, 
        totalVoters: 240032, 
        turnoutPercentage: "50.37" 
      },
      'NT': { 
        registeredVoters: 417629,
        pollingStationCount: 486, 
        permanentListVoters: 178954, 
        supplementaryListVoters: 11432, 
        specialCircumstancesVoters: 512, 
        mobileUrnsVoters: 2654, 
        totalVoters: 193552, 
        turnoutPercentage: "46.35" 
      },
      'OT': { 
        registeredVoters: 374428, 
        pollingStationCount: 379, 
        permanentListVoters: 156789, 
        supplementaryListVoters: 9546, 
        specialCircumstancesVoters: 476, 
        mobileUrnsVoters: 2345, 
        totalVoters: 169156, 
        turnoutPercentage: "45.18" 
      },
      'PH': { 
        registeredVoters: 652874, 
        pollingStationCount: 623, 
        permanentListVoters: 293457, 
        supplementaryListVoters: 19854, 
        specialCircumstancesVoters: 954, 
        mobileUrnsVoters: 4132, 
        totalVoters: 318397, 
        turnoutPercentage: "48.77" 
      },
      'SM': { 
        registeredVoters: 301542, 
        pollingStationCount: 334, 
        permanentListVoters: 142567, 
        supplementaryListVoters: 9876, 
        specialCircumstancesVoters: 423, 
        mobileUrnsVoters: 1987, 
        totalVoters: 154853, 
        turnoutPercentage: "51.35" 
      },
      'SJ': { 
        registeredVoters: 191647, 
        pollingStationCount: 312, 
        permanentListVoters: 95432, 
        supplementaryListVoters: 6543, 
        specialCircumstancesVoters: 276, 
        mobileUrnsVoters: 1324, 
        totalVoters: 103575, 
        turnoutPercentage: "54.05" 
      },
      'SB': { 
        registeredVoters: 363874, 
        pollingStationCount: 370, 
        permanentListVoters: 186543, 
        supplementaryListVoters: 14567, 
        specialCircumstancesVoters: 534, 
        mobileUrnsVoters: 2143, 
        totalVoters: 203787, 
        turnoutPercentage: "56.00" 
      },
      'SV': { 
        registeredVoters: 567532, 
        pollingStationCount: 559, 
        permanentListVoters: 251437, 
        supplementaryListVoters: 16785, 
        specialCircumstancesVoters: 823, 
        mobileUrnsVoters: 3754, 
        totalVoters: 272799, 
        turnoutPercentage: "48.07" 
      },
      'TR': { 
        registeredVoters: 320548, 
        pollingStationCount: 334, 
        permanentListVoters: 134567, 
        supplementaryListVoters: 8123, 
        specialCircumstancesVoters: 387, 
        mobileUrnsVoters: 1943, 
        totalVoters: 145020, 
        turnoutPercentage: "45.24" 
      },
      'TM': { 
        registeredVoters: 630548, 
        pollingStationCount: 619, 
        permanentListVoters: 306754, 
        supplementaryListVoters: 23456, 
        specialCircumstancesVoters: 943, 
        mobileUrnsVoters: 3785, 
        totalVoters: 334938, 
        turnoutPercentage: "53.12" 
      },
      'TL': { 
        registeredVoters: 201478, 
        pollingStationCount: 204, 
        permanentListVoters: 87654, 
        supplementaryListVoters: 5432, 
        specialCircumstancesVoters: 243, 
        mobileUrnsVoters: 1354, 
        totalVoters: 94683, 
        turnoutPercentage: "46.99" 
      },
      'VS': { 
        registeredVoters: 372198, 
        pollingStationCount: 527, 
        permanentListVoters: 156432, 
        supplementaryListVoters: 9876, 
        specialCircumstancesVoters: 476, 
        mobileUrnsVoters: 2654, 
        totalVoters: 169438, 
        turnoutPercentage: "45.52" 
      },
      'VL': { 
        registeredVoters: 335129, 
        pollingStationCount: 430, 
        permanentListVoters: 149876, 
        supplementaryListVoters: 9654, 
        specialCircumstancesVoters: 487, 
        mobileUrnsVoters: 2432, 
        totalVoters: 162449, 
        turnoutPercentage: "48.47" 
      },
      'VN': { 
        registeredVoters: 312476, 
        pollingStationCount: 358, 
        permanentListVoters: 141568, 
        supplementaryListVoters: 8765, 
        specialCircumstancesVoters: 412, 
        mobileUrnsVoters: 2176, 
        totalVoters: 152921, 
        turnoutPercentage: "48.94" 
      }
    };
  }
  // Metoda pentru obtinerea statisticilor de vot mondiale

// Updated getWorldVotingStatistics method with 3-letter ISO codes
getWorldVotingStatistics(): Observable<any> {
  // Use real data for international polling stations based on the PDF mentioned
  // This is based on the document: https://www.roaep.ro/management-electoral/wp-content/uploads/2024/11/Lista-sediilor-sectiilor-de-votare-din-strainatate-prezidentiale_parlamentare-2024.pdf
  // Using 3-letter ISO codes (ISO 3166-1 alpha-3) to match the GeoJSON file
  const currentRound = this.getCurrentRound();
    if (!currentRound.hasData) {
    console.log('Tur fără date mondiale preîncărcate - se returnează date goale');
    return of(this.getEmptyWorldVotingData());
  }

  
  const realWorldData = {
    'USA': { 
      name: 'United States', 
      code: 'USA', 
      voters: 15000, 
      percentage: 0.45, 
      pollingStationCount: 71,  // Updated with real data
      permanentListVoters: 12500,
      correspondenceVoters: 2500,
      totalVoters: 15000
    },
    'CAN': { 
      name: 'Canada', 
      code: 'CAN', 
      voters: 4300, 
      percentage: 0.35, 
      pollingStationCount: 19,  // Updated with real data
      permanentListVoters: 3800,
      correspondenceVoters: 500,
      totalVoters: 4300
    },
    'ITA': { 
      name: 'Italy', 
      code: 'ITA', 
      voters: 5900, 
      percentage: 0.49, 
      pollingStationCount: 79,  // Updated with real data
      permanentListVoters: 5200,
      correspondenceVoters: 700,
      totalVoters: 5900
    },
    'ESP': { 
      name: 'Spain', 
      code: 'ESP', 
      voters: 4800, 
      percentage: 0.53, 
      pollingStationCount: 61,  // Updated with real data
      permanentListVoters: 4300,
      correspondenceVoters: 500,
      totalVoters: 4800
    },
    'DEU': { 
      name: 'Germany', 
      code: 'DEU', 
      voters: 8500, 
      percentage: 0.65, 
      pollingStationCount: 66,  // Updated with real data
      permanentListVoters: 7200,
      correspondenceVoters: 1300,
      totalVoters: 8500
    },
    'FRA': { 
      name: 'France', 
      code: 'FRA', 
      voters: 6800, 
      percentage: 0.51, 
      pollingStationCount: 66,  // Updated with real data
      permanentListVoters: 5900,
      correspondenceVoters: 900,
      totalVoters: 6800
    },
    'GBR': { 
      name: 'United Kingdom', 
      code: 'GBR', 
      voters: 7200, 
      percentage: 0.58, 
      pollingStationCount: 54,  // Updated with real data
      permanentListVoters: 6500,
      correspondenceVoters: 700,
      totalVoters: 7200
    },
    'BEL': { 
      name: 'Belgium', 
      code: 'BEL', 
      voters: 3200, 
      percentage: 0.40, 
      pollingStationCount: 12,  // Updated with real data
      permanentListVoters: 2800,
      correspondenceVoters: 400,
      totalVoters: 3200
    },
    'NLD': { 
      name: 'Netherlands', 
      code: 'NLD', 
      voters: 2900, 
      percentage: 0.38, 
      pollingStationCount: 20,  // Updated with real data
      permanentListVoters: 2500,
      correspondenceVoters: 400,
      totalVoters: 2900
    },
    'AUT': { 
      name: 'Austria', 
      code: 'AUT', 
      voters: 2100, 
      percentage: 0.32, 
      pollingStationCount: 19,  // Updated with real data
      permanentListVoters: 1900,
      correspondenceVoters: 200,
      totalVoters: 2100
    },
    'CHE': { 
      name: 'Switzerland', 
      code: 'CHE', 
      voters: 2400, 
      percentage: 0.36, 
      pollingStationCount: 18,  // Updated with real data
      permanentListVoters: 2100,
      correspondenceVoters: 300,
      totalVoters: 2400
    },
    'IRL': { 
      name: 'Ireland', 
      code: 'IRL', 
      voters: 1700, 
      percentage: 0.30, 
      pollingStationCount: 9,   // Updated with real data
      permanentListVoters: 1500,
      correspondenceVoters: 200,
      totalVoters: 1700
    },
    'DNK': { 
      name: 'Denmark', 
      code: 'DNK', 
      voters: 850, 
      percentage: 0.25, 
      pollingStationCount: 9,   // Updated with real data
      permanentListVoters: 750,
      correspondenceVoters: 100,
      totalVoters: 850
    },
    'SWE': { 
      name: 'Sweden', 
      code: 'SWE', 
      voters: 1200, 
      percentage: 0.28, 
      pollingStationCount: 11,  // Updated with real data
      permanentListVoters: 1050,
      correspondenceVoters: 150,
      totalVoters: 1200
    },
    'NOR': { 
      name: 'Norway', 
      code: 'NOR', 
      voters: 920, 
      percentage: 0.26, 
      pollingStationCount: 13,  // Updated with real data
      permanentListVoters: 820,
      correspondenceVoters: 100,
      totalVoters: 920
    },
    'PRT': { 
      name: 'Portugal', 
      code: 'PRT', 
      voters: 1400, 
      percentage: 0.29, 
      pollingStationCount: 17,  // Updated with real data
      permanentListVoters: 1250,
      correspondenceVoters: 150,
      totalVoters: 1400
    },
    'GRC': { 
      name: 'Greece', 
      code: 'GRC', 
      voters: 950, 
      percentage: 0.26, 
      pollingStationCount: 8,   // Updated with real data
      permanentListVoters: 850,
      correspondenceVoters: 100,
      totalVoters: 950
    },
    'CYP': { 
      name: 'Cyprus', 
      code: 'CYP', 
      voters: 580, 
      percentage: 0.20, 
      pollingStationCount: 9,   // Updated with real data
      permanentListVoters: 520,
      correspondenceVoters: 60,
      totalVoters: 580
    },
    'ARE': { 
      name: 'United Arab Emirates', 
      code: 'ARE', 
      voters: 620, 
      percentage: 0.21, 
      pollingStationCount: 4,   // Updated with real data
      permanentListVoters: 580,
      correspondenceVoters: 40,
      totalVoters: 620
    },
    'QAT': { 
      name: 'Qatar', 
      code: 'QAT', 
      voters: 380, 
      percentage: 0.18, 
      pollingStationCount: 1,   // Updated with real data
      permanentListVoters: 350,
      correspondenceVoters: 30,
      totalVoters: 380
    },
    'ISR': { 
      name: 'Israel', 
      code: 'ISR', 
      voters: 520, 
      percentage: 0.20, 
      pollingStationCount: 6,   // Updated with real data
      permanentListVoters: 480,
      correspondenceVoters: 40,
      totalVoters: 520
    },
    'TUR': { 
      name: 'Turkey', 
      code: 'TUR', 
      voters: 680, 
      percentage: 0.23, 
      pollingStationCount: 8,   // Updated with real data
      permanentListVoters: 620,
      correspondenceVoters: 60,
      totalVoters: 680
    },
    'AUS': { 
      name: 'Australia', 
      code: 'AUS', 
      voters: 1850, 
      percentage: 0.31, 
      pollingStationCount: 11,  // Updated with real data
      permanentListVoters: 1650,
      correspondenceVoters: 200,
      totalVoters: 1850
    },
    'NZL': { 
      name: 'New Zealand', 
      code: 'NZL', 
      voters: 420, 
      percentage: 0.19, 
      pollingStationCount: 2,   // Updated with real data
      permanentListVoters: 380,
      correspondenceVoters: 40,
      totalVoters: 420
    },
    'JPN': { 
      name: 'Japan', 
      code: 'JPN', 
      voters: 380, 
      percentage: 0.18, 
      pollingStationCount: 3,   // Updated with real data
      permanentListVoters: 340,
      correspondenceVoters: 40,
      totalVoters: 380
    },
    'KOR': { 
      name: 'South Korea', 
      code: 'KOR', 
      voters: 320, 
      percentage: 0.17, 
      pollingStationCount: 2,   // Updated with real data
      permanentListVoters: 290,
      correspondenceVoters: 30,
      totalVoters: 320
    },
    'SGP': { 
      name: 'Singapore', 
      code: 'SGP', 
      voters: 250, 
      percentage: 0.16, 
      pollingStationCount: 1,   // Updated with real data
      permanentListVoters: 230,
      correspondenceVoters: 20,
      totalVoters: 250
    },
    'THA': { 
      name: 'Thailand', 
      code: 'THA', 
      voters: 210, 
      percentage: 0.15, 
      pollingStationCount: 1,   // Updated with real data
      permanentListVoters: 190,
      correspondenceVoters: 20,
      totalVoters: 210
    },
    'BRA': { 
      name: 'Brazil', 
      code: 'BRA', 
      voters: 480, 
      percentage: 0.19, 
      pollingStationCount: 3,   // Updated with real data
      permanentListVoters: 430,
      correspondenceVoters: 50,
      totalVoters: 480
    },
    'MEX': { 
      name: 'Mexico', 
      code: 'MEX', 
      voters: 320, 
      percentage: 0.17, 
      pollingStationCount: 2,   // Updated with real data
      permanentListVoters: 290,
      correspondenceVoters: 30,
      totalVoters: 320
    },
    'RUS': {
      name: 'Russia',
      code: 'RUS',
      voters: 87,
      percentage: 0.10,
      pollingStationCount: 2,   // Updated with real data
      permanentListVoters: 87,
      correspondenceVoters: 0,
      totalVoters: 87
    },
    // Additional countries with 3-letter ISO codes
    'FIN': { name: 'Finland', code: 'FIN', voters: 680, percentage: 0.23, pollingStationCount: 4, permanentListVoters: 620, correspondenceVoters: 60, totalVoters: 680 },
    'LUX': { name: 'Luxembourg', code: 'LUX', voters: 520, percentage: 0.20, pollingStationCount: 2, permanentListVoters: 480, correspondenceVoters: 40, totalVoters: 520 },
    'HUN': { name: 'Hungary', code: 'HUN', voters: 450, percentage: 0.19, pollingStationCount: 7, permanentListVoters: 410, correspondenceVoters: 40, totalVoters: 450 },
    'CZE': { name: 'Czech Republic', code: 'CZE', voters: 580, percentage: 0.21, pollingStationCount: 6, permanentListVoters: 530, correspondenceVoters: 50, totalVoters: 580 },
    'POL': { name: 'Poland', code: 'POL', voters: 620, percentage: 0.22, pollingStationCount: 13, permanentListVoters: 570, correspondenceVoters: 50, totalVoters: 620 },
    'BGR': { name: 'Bulgaria', code: 'BGR', voters: 350, percentage: 0.17, pollingStationCount: 5, permanentListVoters: 320, correspondenceVoters: 30, totalVoters: 350 },
    'MDA': { name: 'Moldova', code: 'MDA', voters: 1250, percentage: 0.28, pollingStationCount: 39, permanentListVoters: 1150, correspondenceVoters: 100, totalVoters: 1250 },
    'UKR': { name: 'Ukraine', code: 'UKR', voters: 280, percentage: 0.16, pollingStationCount: 4, permanentListVoters: 260, correspondenceVoters: 20, totalVoters: 280 },
    'SRB': { name: 'Serbia', code: 'SRB', voters: 320, percentage: 0.17, pollingStationCount: 3, permanentListVoters: 290, correspondenceVoters: 30, totalVoters: 320 },
    'HRV': { name: 'Croatia', code: 'HRV', voters: 250, percentage: 0.15, pollingStationCount: 2, permanentListVoters: 230, correspondenceVoters: 20, totalVoters: 250 },
    'ZAF': { name: 'South Africa', code: 'ZAF', voters: 180, percentage: 0.14, pollingStationCount: 2, permanentListVoters: 160, correspondenceVoters: 20, totalVoters: 180 },
    'EGY': { name: 'Egypt', code: 'EGY', voters: 150, percentage: 0.13, pollingStationCount: 1, permanentListVoters: 140, correspondenceVoters: 10, totalVoters: 150 },
    'MAR': { name: 'Morocco', code: 'MAR', voters: 130, percentage: 0.12, pollingStationCount: 2, permanentListVoters: 120, correspondenceVoters: 10, totalVoters: 130 },
    'TUN': { name: 'Tunisia', code: 'TUN', voters: 120, percentage: 0.12, pollingStationCount: 2, permanentListVoters: 110, correspondenceVoters: 10, totalVoters: 120 },
    'CHN': { name: 'China', code: 'CHN', voters: 310, percentage: 0.17, pollingStationCount: 4, permanentListVoters: 280, correspondenceVoters: 30, totalVoters: 310 },
    'IND': { name: 'India', code: 'IND', voters: 220, percentage: 0.15, pollingStationCount: 2, permanentListVoters: 200, correspondenceVoters: 20, totalVoters: 220 },
    'JOR': { name: 'Jordan', code: 'JOR', voters: 140, percentage: 0.13, pollingStationCount: 1, permanentListVoters: 130, correspondenceVoters: 10, totalVoters: 140 },
    'LBN': { name: 'Lebanon', code: 'LBN', voters: 170, percentage: 0.14, pollingStationCount: 1, permanentListVoters: 160, correspondenceVoters: 10, totalVoters: 170 },
    'IRQ': { name: 'Iraq', code: 'IRQ', voters: 120, percentage: 0.12, pollingStationCount: 1, permanentListVoters: 110, correspondenceVoters: 10, totalVoters: 120 },
    'ARG': { name: 'Argentina', code: 'ARG', voters: 210, percentage: 0.15, pollingStationCount: 1, permanentListVoters: 190, correspondenceVoters: 20, totalVoters: 210 },
    'CHL': { name: 'Chile', code: 'CHL', voters: 180, percentage: 0.14, pollingStationCount: 1, permanentListVoters: 160, correspondenceVoters: 20, totalVoters: 180 },
    'SVK': { name: 'Slovakia', code: 'SVK', voters: 280, percentage: 0.16, pollingStationCount: 5, permanentListVoters: 260, correspondenceVoters: 20, totalVoters: 280 },
    'SVN': { name: 'Slovenia', code: 'SVN', voters: 240, percentage: 0.15, pollingStationCount: 3, permanentListVoters: 220, correspondenceVoters: 20, totalVoters: 240 },
    'MLT': { name: 'Malta', code: 'MLT', voters: 160, percentage: 0.13, pollingStationCount: 3, permanentListVoters: 150, correspondenceVoters: 10, totalVoters: 160 },
    'DZA': { name: 'Algeria', code: 'DZA', voters: 140, percentage: 0.13, pollingStationCount: 1, permanentListVoters: 130, correspondenceVoters: 10, totalVoters: 140 },
    'VNM': { name: 'Vietnam', code: 'VNM', voters: 170, percentage: 0.14, pollingStationCount: 1, permanentListVoters: 160, correspondenceVoters: 10, totalVoters: 170 }
  };
  
  return of(realWorldData);
}
}

