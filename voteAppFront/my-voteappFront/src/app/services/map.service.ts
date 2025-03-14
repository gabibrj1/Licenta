import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
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

@Injectable({
  providedIn: 'root'
})
export class MapService {
  // URL-ul API
  private apiUrl = environment.apiUrl;
  
  // Path for GeoJSON and CSV
  private geoJsonPath = 'assets/maps/romania.geojson';
  private csvPath = 'assets/data/presence_2024-12-06.csv';

  constructor(private http: HttpClient) { }

  /**
   * Fetches map information from the API
   */
  getMapInfo(): Observable<MapInfo> {
    console.log('Serviciu: Încercare de a obține date hartă');
    
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
   * Fetches and processes voting statistics from CSV file
   */
/**
 * Fetches and processes voting statistics from CSV file
 */
getVotingStatistics(): Observable<any> {
  console.log('Încercare încărcare CSV de la:', this.csvPath);
  
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
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'AR': { 
        registeredVoters: 372641, 
        pollingStationCount: 437, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'AG': { 
        registeredVoters: 511368, 
        pollingStationCount: 520, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'BC': { 
        registeredVoters: 583217, 
        pollingStationCount: 634, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'BH': { 
        registeredVoters: 499754, 
        pollingStationCount: 652, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'BN': { 
        registeredVoters: 244327, 
        pollingStationCount: 313, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'BT': { 
        registeredVoters: 350872, 
        pollingStationCount: 422, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'BV': { 
        registeredVoters: 512742, 
        pollingStationCount: 447, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'BR': { 
        registeredVoters: 294250, 
        pollingStationCount: 281, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'B': { 
        registeredVoters: 1794329, 
        pollingStationCount: 1274, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'BZ': { 
        registeredVoters: 380123, 
        pollingStationCount: 427, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'CS': { 
        registeredVoters: 266235, 
        pollingStationCount: 365, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'CL': { 
        registeredVoters: 266412, 
        pollingStationCount: 235, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'CJ': { 
        registeredVoters: 630548, 
        pollingStationCount: 619, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'CT': { 
        registeredVoters: 631429, 
        pollingStationCount: 556, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'CV': { 
        registeredVoters: 181579, 
        pollingStationCount: 214, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'DB': { 
        registeredVoters: 423721, 
        pollingStationCount: 432, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'DJ': { 
        registeredVoters: 562763, 
        pollingStationCount: 529, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'GL': { 
        registeredVoters: 518289, 
        pollingStationCount: 436, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'GR': { 
        registeredVoters: 230742, 
        pollingStationCount: 245, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'GJ': { 
        registeredVoters: 301529, 
        pollingStationCount: 332, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'HR': { 
        registeredVoters: 267982, 
        pollingStationCount: 290, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'HD': { 
        registeredVoters: 379254, 
        pollingStationCount: 524, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'IL': { 
        registeredVoters: 245327, 
        pollingStationCount: 220, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'IS': { 
        registeredVoters: 730541, 
        pollingStationCount: 755, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'IF': { 
        registeredVoters: 389764, 
        pollingStationCount: 255, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'MM': { 
        registeredVoters: 418965, 
        pollingStationCount: 435, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'MH': { 
        registeredVoters: 242358, 
        pollingStationCount: 286, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'MS': { 
        registeredVoters: 476541, 
        pollingStationCount: 568, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
'NT': { 
        registeredVoters: 417629,
        pollingStationCount: 486, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'OT': { 
        registeredVoters: 374428, 
        pollingStationCount: 379, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'PH': { 
        registeredVoters: 652874, 
        pollingStationCount: 623, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'SM': { 
        registeredVoters: 301542, 
        pollingStationCount: 334, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'SJ': { 
        registeredVoters: 191647, 
        pollingStationCount: 312, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'SB': { 
        registeredVoters: 363874, 
        pollingStationCount: 370, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'SV': { 
        registeredVoters: 567532, 
        pollingStationCount: 559, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'TR': { 
        registeredVoters: 320548, 
        pollingStationCount: 334, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'TM': { 
        registeredVoters: 630548, 
        pollingStationCount: 619, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'TL': { 
        registeredVoters: 201478, 
        pollingStationCount: 204, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'VS': { 
        registeredVoters: 372198, 
        pollingStationCount: 527, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'VL': { 
        registeredVoters: 335129, 
        pollingStationCount: 430, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      },
      'VN': { 
        registeredVoters: 312476, 
        pollingStationCount: 358, 
        permanentListVoters: 0, 
        supplementaryListVoters: 0, 
        specialCircumstancesVoters: 0, 
        mobileUrnsVoters: 0, 
        totalVoters: 0, 
        turnoutPercentage: "0.00" 
      }
    };
  }
}