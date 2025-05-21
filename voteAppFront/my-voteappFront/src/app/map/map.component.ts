import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, Renderer2, NgZone, HostListener, OnDestroy  } from '@angular/core';
import { MapService, MapInfo, ElectionRoundState } from '../services/map.service';
import * as d3 from 'd3';
import { Router } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';


interface CountyData {
  name: string;
  code: string;
  voters: number;
  percentage: number;
   // Campuri pentru statistici
  registeredVoters?: number;
  pollingStationCount?: number;
  permanentListVoters?: number;
  supplementaryListVoters?: number;
  specialCircumstancesVoters?: number;
  mobileUrnsVoters?: number;
  correspondenceVoters?: number;
  totalVoters?: number;
  turnoutPercentage?: number;
}

interface GeoFeature {
  type: string;
  properties: {
    name: string;
    code?: string;
  };
  geometry: any;
}

interface GeoJSONFeature {
  type: string;
  geometry: any;
  properties: {
    name: string;
    [key: string]: any;
  };
}

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})
export class MapComponent implements OnInit, AfterViewInit {
  @ViewChild('mapContainer') mapContainer!: ElementRef;
  
  // Configurare harta
  mapLevel: string = 'judete';
  highlightField: string = 'prezenta';
  relativeTo: string = 'maxim';

  private pollingInterval: any = null;
  private shouldPoll: boolean = false;


  // Valorile pentru filtrare
  filterPercentage: number = 0;

  // Starea turului curent
currentRoundState: ElectionRoundState = {
  roundId: 'tur1_2024',
  hasData: true
};

private roundSubscription: Subscription;
  
  // Data
  geoJsonData: any = null;
  countyData: { [key: string]: CountyData } = {};
  
  // UI state
  isLoading: boolean = true;
  hoveredCounty: CountyData | null = null;
  hoverPosition = { x: 0, y: 0 };
  
  // Statistici
  totalVoters: string = '53.675';
  totalPercentage: string = '0.30';
  maxValue: string = '100';
  minValue: string = '0';
  appVersion: string = '6.22.11.19';
  
  // Variabile pentru harta
  private svg: any;
  private projection: any;
  private path: any;
  private zoom: any;
  private g: any;
  private currentTransform: any = { k: 1, x: 0, y: 0 };
  private skipCountyMapLoad: boolean = false;

  // Variabile pentru harta cu UAT-uri
  selectedCounty: string | null = null;
  uatGeoJsonData: any = null;
  isUATView: boolean = false;
  countyOptions: {code: string, name: string}[] = [];

  // Variabile pentru comutarea la harta lumii
  mapLocation: string = 'romania';
  worldGeoJsonData: any = null;
  countryData: { [key: string]: CountyData } = {};
  hoveredCountry: CountyData | null = null;

  // Variabile pentru harta internationala
  private worldMapZoom: number = 1;
  // Min and max zoom constraints
  private minZoom: number = 0.5;
  private maxZoom: number = 3;
  // Zoom step size
  private zoomStep: number = 0.1;

  


  constructor(
    private mapService: MapService,
    private renderer: Renderer2,
    private ngZone: NgZone,
    private router: Router,
    private route: ActivatedRoute
  ) {
      this.roundSubscription = this.mapService.currentRound$.subscribe(roundState => {
    console.log('MapComponent: S-a detectat schimbarea turului:', roundState);
    
    // Actualizăm starea turului
    this.currentRoundState = roundState;
    
    // Reîncărcăm datele hartă dacă este deja inițializată
    if (this.svg) {
      console.log('Reîncărcare hartă după schimbarea turului');
      this.reloadMapData();
    }
  });
  }
  navigateToHome(): void {
    this.router.navigate(['']);
  }


  // Redimensionare harta
  @HostListener('window:resize')
  onResize() {
    this.resizeMap();
  }

ngOnInit(): void {
  console.log('MapComponent: ngOnInit a fost apelat');
    this.roundSubscription = this.mapService.currentRound$.subscribe(roundState => {
    console.log('MapComponent: S-a detectat schimbarea turului:', roundState);
    
    // Actualizăm starea turului
    this.currentRoundState = roundState;
    
    // Oprim polling-ul dacă exista
    this.stopPolling();
    
    // Dacă e tur activ, pornește polling-ul
    if (roundState.roundId === 'tur_activ') {
      this.shouldPoll = true;
      this.startPolling();
    } else {
      this.shouldPoll = false;
    }
    
    // Reîncărcăm datele hartă dacă este deja inițializată
    if (this.svg) {
      console.log('Reîncărcare hartă după schimbarea turului');
      this.reloadMapData();
    }
  });
  

  
  // Verificăm query parameters pentru locație și tur
  this.route.queryParams.subscribe(params => {
    // Verifică dacă avem parametri pentru UAT
    const hasUATParams = params['uatView'] === 'true' && params['county'];
    
    // Setăm flag-ul pentru a sări peste încărcarea hărții de județe dacă avem parametri UAT
    this.skipCountyMapLoad = hasUATParams;
    
    // Actualizăm locația
    if (params['location']) {
      this.mapLocation = params['location'];
    }
    
    // Actualizăm turul dacă este specificat
    if (params['round']) {
      const roundId = params['round'];
      const hasData = roundId === 'tur1_2024'; // Doar turul 1 are date, turul 2 și activ nu au
      
      console.log(`MapComponent: Setare tur din parametri - ${roundId}, hasData: ${hasData}`);
      
      // Actualizăm serviciul cu noul tur
      this.mapService.setCurrentRound(roundId, hasData);
      
      // Actualizăm starea turului în componentă
      this.currentRoundState = {
        roundId: roundId,
        hasData: hasData
      };
    }
    
    // Forțăm reîncărcarea hărții de fiecare dată
    this.isLoading = true;
    
    // Încărcăm harta corespunzătoare
    if (this.mapLocation === 'romania') {
      if (hasUATParams) {
        // Încărcăm direct harta UAT fără a mai încărca harta județelor
        console.log('Încărcăm direct vizualizarea UAT din parametrii URL:', params['county']);
        this.mapLevel = 'uaturi';
        this.loadCountyUATMap(params['county']);
      } else {
        // Încărcăm harta județelor normală
        this.loadMapData();
      }
    } else {
      this.loadWorldMapData();
    }
  });
}
startPolling(): void {
  console.log('Pornire polling date tur activ');
  // Oprim orice interval existent
  this.stopPolling();
  
  // Pornim un nou interval - actualizare la fiecare 10 secunde
  this.pollingInterval = setInterval(() => {
    if (this.shouldPoll && this.currentRoundState.roundId === 'tur_activ') {
      console.log('Actualizare date tur activ prin polling');
      this.loadActiveRoundData();
    }
  }, 10000); // 10 secunde
}

stopPolling(): void {
  if (this.pollingInterval) {
    clearInterval(this.pollingInterval);
    this.pollingInterval = null;
  }
}

forceMapReload(): void {
  console.log('Forțăm reîncărcarea hărții cu noile date');
  
  // Golim datele hartă
  this.geoJsonData = null;
  this.worldGeoJsonData = null;
  
  // Setăm flag-ul de încărcare
  this.isLoading = true;
  
  // Înlăturăm SVG-ul existent
  if (this.svg) {
    this.svg.remove();
    this.svg = null;
  }
  
  // Reîncărcăm datele corespunzătoare
  if (this.mapLocation === 'romania') {
    this.loadMapData();
  } else {
    this.loadWorldMapData();
  }
}


reloadMapData(): void {
  console.log('Reîncărcăm datele hartă pentru noul tur:', this.currentRoundState);
  
  // Verifică dacă suntem deja în vizualizare UAT
  if (this.isUATView && this.selectedCounty) {
    console.log('Suntem deja în vizualizare UAT, vom încărca direct UAT pentru:', this.selectedCounty);
    
    // Nu încărcăm harta județelor, ci direct UAT
    this.skipCountyMapLoad = true;
    this.loadCountyUATMap(this.selectedCounty);
    return;
  }
  
  this.isLoading = true;
  
  // Încărcăm harta corespunzătoare
  if (this.mapLocation === 'romania') {
    this.loadMapData();
  } else {
    this.loadWorldMapData();
  }
}

  ngAfterViewInit(): void {
    // Initialize map when the view is ready
    if (!this.isLoading && this.geoJsonData) {
      this.initializeMap();
    }
  }

ngOnDestroy(): void {
  // Anulăm subscripția pentru a evita memory leak
  if (this.roundSubscription) {
    this.roundSubscription.unsubscribe();
  }
  
  // Oprim polling-ul
  this.stopPolling();
}

  // Metoda pentru comutare intre harti
  setMapLocation(location: string): void {
    if (this.mapLocation === location) return;
    
    this.mapLocation = location;
    this.isLoading = true;
    
    if (location === 'romania') {
      this.loadMapData();
    } else {
      this.loadWorldMapData();
    }
  }
  /**
 * Mărește nivelul de zoom pentru harta mondială
 */
zoomIn(): void {
  if (this.worldMapZoom < this.maxZoom) {
    this.worldMapZoom += this.zoomStep;
    this.applyWorldMapZoom();
  }
}

/**
 * Reduce nivelul de zoom pentru harta mondială
 */
zoomOut(): void {
  if (this.worldMapZoom > this.minZoom) {
    this.worldMapZoom -= this.zoomStep;
    this.applyWorldMapZoom();
  }
}

/**
 * Aplică nivelul curent de zoom la SVG-ul hărții mondiale
 */
private applyWorldMapZoom(): void {
  if (this.mapLocation === 'strainatate' && this.svg) {
    this.ngZone.runOutsideAngular(() => {
      // Calculează transformarea D3 pentru zoom
      const width = this.mapContainer.nativeElement.clientWidth;
      const height = this.mapContainer.nativeElement.clientHeight;
      const centerX = width / 2;
      const centerY = height / 2;
      
      // Aplică zoom-ul păstrând centrul
      const transform = d3.zoomIdentity
        .translate(centerX, centerY)
        .scale(this.worldMapZoom)
        .translate(-centerX, -centerY);
      
      // Aplică transformarea cu animație
      this.svg.transition()
        .duration(300)
        .call(this.zoom.transform, transform);
        
      // Ajustează dimensiunea textului în funcție de zoom
      const fontSize = 12 / this.worldMapZoom;
      const smallerFontSize = 10 / this.worldMapZoom;
      
      // Update text sizes for different label types
      this.g.selectAll('.country-label')
        .attr('font-size', `${fontSize}px`);
      
      this.g.selectAll('.polling-station-count')
        .attr('font-size', `${fontSize}px`);
        
      this.g.selectAll('.country-voters')
        .attr('font-size', `${smallerFontSize}px`);
    });
  }
}
updateCountryLabels(): void {
  if (this.mapLocation === 'strainatate' && this.g) {
    // Clear and recreate labels
    this.addCountryLabels();
    
    // Update colors of countries
    this.g.selectAll('.country-path')
      .attr('fill', (d: GeoFeature) => this.getCountryColor(this.getCountryCode(d)));
  }
}
  // Metoda pentru incarcarea datelor hartii mondiale
loadWorldMapData(): void {
  this.mapLocation = 'strainatate';
  console.log('MapComponent: Începe încărcarea datelor hartă mondială pentru turul:', this.currentRoundState.roundId);
  this.isLoading = true;
  
  // Verifică dacă turul curent are date
  if (!this.currentRoundState.hasData) {
    console.log('Turul curent nu are date - se afișează hartă mondială goală');
    
    // Încarcă doar structura geografică, nu și datele statistice
    this.loadWorldGeoJsonData().then(geoData => {
      this.worldGeoJsonData = geoData;
      
      // Creează date goale pentru țări
      const emptyCountryData: { [key: string]: CountyData } = {};
      
      // Inițializează date goale pentru țările din structura geografică
      geoData.features.forEach((feature: GeoFeature) => {
        const countryCode = this.getCountryCode(feature);
        
        // Evită adăugarea țărilor invalide sau non-țări
        const invalidCodes = ['ATA', 'AQ', 'Unknown', 'Antarctica', 'Bermuda', 'Ber'];
        if (!invalidCodes.includes(countryCode) && !invalidCodes.includes(feature.properties.name)) {
          emptyCountryData[countryCode] = {
            name: feature.properties.name,
            code: countryCode,
            voters: 0,
            percentage: 0,
            pollingStationCount: 0,
            permanentListVoters: 0,
            correspondenceVoters: 0,
            totalVoters: 0
          };
        }
      });
      
      this.countryData = emptyCountryData;
      this.isLoading = false;
      
      // Actualizăm valorile de statistici globale
      this.totalVoters = '0';
      this.totalPercentage = '0.00';
      
      setTimeout(() => {
        this.initializeWorldMap();
      }, 100);
    }).catch(error => {
      console.error('Eroare la încărcarea GeoJSON pentru harta lumii:', error);
      this.isLoading = false;
    });
    
    return;
  }
  
  this.loadWorldGeoJsonData().then(geoData => {
    console.log('MapComponent: Date GeoJSON hartă mondială primite cu succes');
    this.worldGeoJsonData = geoData;
    
    this.mapService.getWorldVotingStatistics().subscribe({
      next: (countryStats: any) => {
        console.log('MapComponent: Date statistice țări primite cu succes');
        this.countryData = countryStats;
        
        // Prelucrare suplimentară a datelor pentru o mai bună vizualizare
        this.preprocessWorldData();
        
        this.isLoading = false;
        
        setTimeout(() => {
          this.initializeWorldMap();
        }, 100);
      },
      error: (error: any) => {
        console.error('MapComponent: Eroare la încărcarea datelor statistice pentru țări:', error);
        this.isLoading = false;
        
        // Încărcăm harta chiar și în caz de eroare, dar cu date goale
        this.countryData = {};
        setTimeout(() => {
          this.initializeWorldMap();
        }, 100);
      }
    });
  }).catch((error: any) => {
    console.error('MapComponent: Eroare la încărcarea GeoJSON pentru harta lumii:', error);
    this.isLoading = false;
  });
}
  private preprocessWorldData(): void {
    // Aici putem adăuga orice logică de preprocesare necesară pentru datele mondiale
    // De exemplu, calcularea procentajelor, normalizarea datelor etc.
    
    // Asigurăm-ne că toate țările au cel puțin valori implicite
    Object.keys(this.countryData).forEach(code => {
      const country = this.countryData[code];
      if (!country.totalVoters) country.totalVoters = 0;
      if (!country.pollingStationCount) country.pollingStationCount = 0;
      if (!country.permanentListVoters) country.permanentListVoters = 0;
      if (!country.correspondenceVoters) country.correspondenceVoters = 0;
    });
  }
  

//  Metoda pentru obtinerea GeoJSON pentru harta lumii
private loadWorldGeoJsonData(): Promise<any> {
  return new Promise((resolve, reject) => {
    fetch('assets/maps/countries.geo.json')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => resolve(data))
      .catch(error => reject(error));
  });
}

// 5. Metoda pentru initializarea hartii mondiale
initializeWorldMap(): void {
  if (!this.worldGeoJsonData || !this.mapContainer) return;
  
  this.ngZone.runOutsideAngular(() => {
    const container = this.mapContainer.nativeElement;
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    
    const width = container.clientWidth;
    const height = container.clientHeight || 500;
    
    this.svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .attr('class', 'world-map');
    
    // Îmbunătățim proiecția pentru o hartă mai clară și mai centrată
    this.projection = d3.geoMercator()
      .center([0, 30]) // Centrare optimizată pentru vizibilitate globală
      .scale(width / 6.5) // Scală inițială mai potrivită
      .translate([width / 2, height / 2]);
    
    this.path = d3.geoPath().projection(this.projection);
    
    this.zoom = d3.zoom()
      .scaleExtent([0.5, 8]) // Min și max zoom
      .translateExtent([[-width, -height], [width * 2, height * 2]])
      .on('zoom', (event) => {
        this.currentTransform = event.transform;
        this.g.attr('transform', event.transform);
        
        // Ajustează grosimea contururilor în funcție de nivelul de zoom
        const strokeWidth = 0.5 / event.transform.k;
        this.g.selectAll('.country-path')
          .attr('stroke-width', strokeWidth);
          
        // Ajustează dimensiunea textului în funcție de zoom
        const fontSize = 10 / event.transform.k;
        this.g.selectAll('.country-label')
          .attr('font-size', `${fontSize}px`);
        this.g.selectAll('.country-voters')
          .attr('font-size', `${fontSize * 0.8}px`);
      });
    
    this.svg.call(this.zoom);
    
    this.g = this.svg.append('g');
    
    // Adăugăm un dreptunghi de fundal pentru interacțiune mai bună
    this.g.append('rect')
      .attr('width', width * 4)
      .attr('height', height * 4)
      .attr('x', -width)
      .attr('y', -height)
      .attr('fill', 'transparent')
      .attr('pointer-events', 'none');
    
    // Lista de coduri/nume de țară care ar trebui ignorate
    const invalidCodes = ['Bermuda','Ber','ATA', 'AQ', 'Unknown', 'Antarctica'];
    
    const countryPaths = this.g.selectAll('.country-path')
      .data(this.worldGeoJsonData.features)
      .enter()
      .append('path')
      .attr('class', 'country-path')
      .attr('id', (d: GeoFeature) => this.getCountryCode(d))
      .attr('d', this.path)
      .attr('fill', (d: GeoFeature) => this.getCountryColor(this.getCountryCode(d)))
      .attr('stroke', 'rgba(255, 255, 255, 0.5)')
      .attr('stroke-width', 0.5);

    // Filtrăm aici doar țările valide pentru evenimente de hover
    countryPaths
      .filter((d: GeoFeature) => {
        const code = this.getCountryCode(d);
        return !invalidCodes.includes(code) && !invalidCodes.includes(d.properties.name);
      })
      .on('mouseover', (event: any, d: GeoFeature) => {
        event.stopPropagation();
        this.ngZone.run(() => this.handleCountryMouseOver(event, d));
      })
      .on('mousemove', (event: any) => {
        event.stopPropagation();
        this.ngZone.run(() => this.handleCountryMouseMove(event));
      })
      .on('mouseout', (event: any, d: GeoFeature) => {
        event.stopPropagation();
        this.ngZone.run(() => this.handleCountryMouseOut(event, d));
      });
    
    // Adăugăm etichetele pentru toate țările
    this.addCountryLabels();
    
    // Adăugăm un handler pentru fundalul hărții pentru a ascunde tooltip-ul când mouse-ul e pe fundal
    this.svg.on('mouseover', () => {
      this.ngZone.run(() => {
        this.hoveredCounty = null;
        this.hoveredCountry = null;
      });
    });
    
    // Efectuăm un zoom inițial pentru a centra harta corect
    const worldMapZoom = 1.2; // Valoare inițială de zoom mai bună
    
    // Aplicăm zoom-ul inițial după o mică întârziere pentru animație fluidă
    setTimeout(() => {
      const centerX = width / 2;
      const centerY = height / 2;
      
      // Aplicăm zoom-ul păstrând centrul
      const transform = d3.zoomIdentity
        .translate(centerX, centerY)
        .scale(worldMapZoom)
        .translate(-centerX, -centerY);
      
      // Aplicăm transformarea cu animație
      this.svg.transition()
        .duration(500)
        .call(this.zoom.transform, transform);
      
      this.ngZone.run(() => {
        this.initializeMapSettings();
      });
    }, 100);
  });
}

private addCountryLabels(): void {
  this.g.selectAll('.country-label, .country-voters, .polling-station-count').remove();
  
  this.worldGeoJsonData.features.forEach((feature: GeoFeature) => {
    const countryCode = this.getCountryCode(feature);
    const invalidCodes = ['ATA', 'AQ', 'Unknown', 'Antarctica', 'Bermuda', 'Ber'];
    
    if (!invalidCodes.includes(countryCode) && !invalidCodes.includes(feature.properties.name)) {
      const centroid = this.path.centroid(feature);
      
      if (!isNaN(centroid[0]) && !isNaN(centroid[1])) {
        const area = this.path.area(feature);
        
        const countryData = this.countryData[countryCode];
        const hasSignificantVotes = countryData && countryData.totalVoters && countryData.totalVoters > 0;
        const hasPollingStations = countryData && countryData.pollingStationCount && countryData.pollingStationCount > 0;
        
        if (area > 3 || hasSignificantVotes || hasPollingStations) {
          if (this.highlightField !== 'sectii' && this.highlightField !== 'votanti') {
            this.g.append('text')
              .attr('class', 'country-label')
              .attr('x', centroid[0])
              .attr('y', centroid[1])
              .attr('text-anchor', 'middle')
              .attr('alignment-baseline', 'middle')
              .attr('fill', 'white')
              .attr('font-size', hasSignificantVotes ? '12px' : '10px')
              .attr('font-weight', 'bold')
              .attr('pointer-events', 'none')
              .text(countryCode);
          }
          
          if (this.highlightField === 'sectii' && hasPollingStations) {
            this.g.append('text')
              .attr('class', 'polling-station-count')
              .attr('x', centroid[0])
              .attr('y', centroid[1])
              .attr('text-anchor', 'middle')
              .attr('alignment-baseline', 'middle')
              .attr('fill', 'white')
              .attr('font-size', '12px')
              .attr('font-weight', 'bold')
              .attr('pointer-events', 'none')
              .text(countryData.pollingStationCount);
          }
          
          if (this.highlightField === 'votanti' && hasSignificantVotes) {
            this.g.append('text')
              .attr('class', 'country-voters')
              .attr('x', centroid[0])
              .attr('y', centroid[1])
              .attr('text-anchor', 'middle')
              .attr('alignment-baseline', 'middle')
              .attr('fill', 'white')
              .attr('font-size', '12px')
              .attr('font-weight', 'bold')
              .attr('pointer-events', 'none')
              .text(this.formatVotersNumber(countryData.totalVoters || 0));
          }
        }
      }
    }
  });
}
// Metoda pentru a obtine codul tarii
getCountryCode(feature: GeoFeature): string {
  // Verifică dacă feature are un id (folosind 'as any' pentru a evita eroarea TypeScript)
  if ((feature as any).id) {
    return (feature as any).id.toString();
  }
  
  // Verifică proprietățile pentru codul ISO sau name
  const props = feature.properties as any;
  
  if (props) {
    // Caută diverse proprietăți posibile pentru cod
    if (props.ISO_A3) return props.ISO_A3;
    if (props.ISO_A2) return props.ISO_A2;
    if (props.iso_a3) return props.iso_a3;
    if (props.iso_a2) return props.iso_a2;
    if (props.code) return props.code;
    
    // Dacă nu există cod, folosește numele
    if (props.name) return props.name;
  }
  
  return 'Unknown';
}
getCountryColor(countryCode: string): string {
  const country = this.countryData[countryCode];
  if (!country) return 'rgba(255, 255, 255, 0.05)';
  
  if (this.highlightField === 'sectii') {
    const stationCount = country.pollingStationCount || 0;
    
    if (stationCount === this.filterPercentage || 
        (stationCount === parseInt(this.maxValue) && this.filterPercentage === parseInt(this.maxValue))) {
      return '#1f1f1f';
    } else if (stationCount > this.filterPercentage) {
      let maxStations = 0;
      Object.values(this.countryData).forEach(c => {
        if (c.pollingStationCount && c.pollingStationCount > maxStations) {
          maxStations = c.pollingStationCount;
        }
      });
      
      const normalizedPercentage = maxStations > 0 ? stationCount / maxStations : 0;
      
      if (normalizedPercentage > 0.6) return '#4050e0';
      if (normalizedPercentage > 0.4) return '#6070e0';
      if (normalizedPercentage > 0.2) return '#8090e0';
      if (normalizedPercentage > 0.1) return '#a0b0e0';
      return '#c0d0ff';
    } else {
      return 'rgba(255, 255, 255, 0.1)';
    }
  }
  else if (this.highlightField === 'votanti') {
    const totalVoters = country.totalVoters || 0;
    
    if (totalVoters === this.filterPercentage || 
        (totalVoters === parseInt(this.maxValue) && this.filterPercentage === parseInt(this.maxValue))) {
      return '#1f1f1f';
    } else if (totalVoters > this.filterPercentage) {
      let maxVoters = 0;
      Object.values(this.countryData).forEach(c => {
        if (c.totalVoters && c.totalVoters > maxVoters) {
          maxVoters = c.totalVoters;
        }
      });
      
      const normalizedPercentage = maxVoters > 0 ? totalVoters / maxVoters : 0;
      
      if (normalizedPercentage > 0.6) return '#4050e0';
      if (normalizedPercentage > 0.4) return '#6070e0';
      if (normalizedPercentage > 0.2) return '#8090e0';
      if (normalizedPercentage > 0.1) return '#a0b0e0';
      return '#c0d0ff';
    } else {
      return 'rgba(255, 255, 255, 0.1)';
    }
  }
  else {
    if (this.highlightField === 'votanti') {
      const totalVoters = country.totalVoters || 0;
      
      if (totalVoters >= this.filterPercentage) {
        return '#1f1f1f';
      }
      
      let maxVoters = 0;
      Object.values(this.countryData).forEach(c => {
        if (c.totalVoters && c.totalVoters > maxVoters) {
          maxVoters = c.totalVoters;
        }
      });
      
      const normalizedPercentage = maxVoters > 0 ? totalVoters / maxVoters : 0;
      
      if (normalizedPercentage > 0.8) return 'rgba(66, 133, 244, 1.0)';
      if (normalizedPercentage > 0.6) return 'rgba(66, 133, 244, 0.8)';
      if (normalizedPercentage > 0.4) return 'rgba(66, 133, 244, 0.6)';
      if (normalizedPercentage > 0.2) return 'rgba(66, 133, 244, 0.4)';
      if (normalizedPercentage > 0.1) return 'rgba(66, 133, 244, 0.25)';
      return 'rgba(66, 133, 244, 0.15)';
    } else {
      const stationCount = country.pollingStationCount || 0;
      
      let maxStations = 0;
      Object.values(this.countryData).forEach(c => {
        if (c.pollingStationCount && c.pollingStationCount > maxStations) {
          maxStations = c.pollingStationCount;
        }
      });
      
      const normalizedPercentage = maxStations > 0 ? stationCount / maxStations : 0;
      
      if (normalizedPercentage > 0.8) return 'rgba(66, 133, 244, 1.0)';
      if (normalizedPercentage > 0.6) return 'rgba(66, 133, 244, 0.8)';
      if (normalizedPercentage > 0.4) return 'rgba(66, 133, 244, 0.6)';
      if (normalizedPercentage > 0.2) return 'rgba(66, 133, 244, 0.4)';
      if (normalizedPercentage > 0.1) return 'rgba(66, 133, 244, 0.25)';
      return 'rgba(66, 133, 244, 0.15)';
    }
  }
}

handleCountryMouseOver(event: any, feature: GeoFeature): void {
  // Obținem codul țării din GeoJSON
  const countryCode = this.getCountryCode(feature);
  
  // Lista de coduri/nume de țară care ar trebui ignorate
  const invalidCodes = ['ATA', 'AQ', 'Unknown', 'Antarctica'];
  
  // Verificăm dacă este un cod/nume de țară de ignorat
  if (invalidCodes.includes(countryCode) || 
      (feature.properties && invalidCodes.includes(feature.properties.name))) {
    return; // Nu facem nimic pentru aceste cazuri
  }
  
  const countryData = this.countryData[countryCode];
  
  // Dacă avem date pentru această țară, le folosim
  if (countryData) {
    this.hoveredCountry = {
      name: countryData.name || feature.properties.name,
      code: countryCode,
      voters: countryData.voters || 0,
      percentage: countryData.percentage || 0,
      
      pollingStationCount: countryData.pollingStationCount || 0,
      permanentListVoters: countryData.permanentListVoters || 0,
      correspondenceVoters: countryData.correspondenceVoters || 0,
      totalVoters: countryData.totalVoters || 0
    };
  } else {
    // Dacă nu avem date, folosim cel puțin numele țării pentru a afișa ceva
    this.hoveredCountry = {
      name: feature.properties.name,
      code: countryCode,
      voters: 0,
      percentage: 0,
      pollingStationCount: 0,
      permanentListVoters: 0,
      correspondenceVoters: 0,
      totalVoters: 0
    };
  }
  
  // Setăm hoveredCounty pentru a afișa tooltip-ul
  this.hoveredCounty = this.hoveredCountry;
  
  // Calculăm poziția tooltip-ului
  const mapRect = this.mapContainer.nativeElement.getBoundingClientRect();
  const x = event.pageX - mapRect.left;
  const y = event.pageY - mapRect.top;
  
  const tooltipWidth = 280;
  const tooltipHeight = 250;
  
  let posX = x;
  let posY = y;
  
  if (x + tooltipWidth > mapRect.width) {
    posX = x - tooltipWidth;
  }
  
  if (y + tooltipHeight > mapRect.height) {
    posY = y - tooltipHeight;
  }
  
  posX = Math.max(10, posX);
  posY = Math.max(10, posY);
  
  this.hoverPosition = {
    x: posX,
    y: posY
  };
  
  // Schimbă culoarea țării
  d3.select(event.target).attr('fill', '#0066cc');
}

handleCountryMouseMove(event: any): void {
  if (!this.hoveredCounty) return;
  
  const mapRect = this.mapContainer.nativeElement.getBoundingClientRect();
  const x = event.clientX - mapRect.left;
  const y = event.clientY - mapRect.top;
  
  const tooltipWidth = 280;
  const tooltipHeight = 250;
  
  let posX = x;
  let posY = y;
  
  if (x + tooltipWidth > mapRect.width) {
    posX = x - tooltipWidth;
  }
  
  if (y + tooltipHeight > mapRect.height) {
    posY = y - tooltipHeight;
  }
  
  posX = Math.max(10, posX);
  posY = Math.max(10, posY);
  
  this.hoverPosition = {
    x: posX,
    y: posY
  };
}

handleCountryMouseOut(event: any, feature: GeoFeature): void {
  const countryCode = this.getCountryCode(feature);
  
  d3.select(event.target)
    .attr('fill', this.getCountryColor(countryCode));
  
  this.hoveredCounty = null;
  this.hoveredCountry = null;
}



loadMapData(): void {
  this.mapLocation = 'romania';
  console.log('MapComponent: Începe încărcarea datelor hartă pentru turul:', this.currentRoundState.roundId);
    // Verifică dacă trebuie să sărim peste încărcarea hărții de județe
  if (this.skipCountyMapLoad) {
    console.log('Se sare peste încărcarea hărții de județe pentru a afișa direct UAT');
    this.isLoading = false;
    this.skipCountyMapLoad = false; // Resetăm flag-ul
    return;
  }
  this.isLoading = true;

    if (this.currentRoundState.roundId === 'tur_activ') {
    // Încarcă datele în timp real pentru turul activ
    this.loadActiveRoundData();
    return;
  }
  
  // Verifică dacă turul curent are date
  if (!this.currentRoundState.hasData) {
    console.log('Turul curent nu are date - se afișează hartă goală');
    
    // Încarcă doar structura geografică, nu și datele statistice
    this.loadGeoJsonData().then(geoData => {
      this.geoJsonData = geoData;
      
      // Creează date goale pentru județe
      const emptyCountyData: { [key: string]: CountyData } = {};
      
      // Inițializează date goale pentru toate județele
      geoData.features.forEach((feature: GeoFeature) => {
        const countyCode = this.getCountyCode(feature);
        emptyCountyData[countyCode] = {
          name: feature.properties.name,
          code: countyCode,
          voters: 0,
          percentage: 0,
          registeredVoters: 0,
          pollingStationCount: 0,
          permanentListVoters: 0,
          supplementaryListVoters: 0,
          specialCircumstancesVoters: 0,
          mobileUrnsVoters: 0,
          totalVoters: 0,
          turnoutPercentage: 0
        };
      });
      
      this.countyData = emptyCountyData;
      this.isLoading = false;
      
      // Actualizăm valorile de statistici globale
      this.totalVoters = '0';
      this.totalPercentage = '0.00';
      
      setTimeout(() => {
        this.initializeMap();
      }, 100);
    }).catch(error => {
      console.error('Eroare la încărcarea GeoJSON:', error);
      this.isLoading = false;
    });
    
    return;
  }



  
  // Incarca statisticile de vot din CSV
  this.mapService.getVotingStatistics().subscribe({
    next: (votingStats) => {
      console.log('MapComponent: Date CSV primite cu succes');
      
      // Incarca datele GeoJSON
      this.loadGeoJsonData().then(geoData => {
        console.log('MapComponent: Date GeoJSON primite cu succes');
        this.geoJsonData = geoData;
        
        // Incarca statistici pentru judete
        this.mapService.getMapInfo().subscribe({
          next: (countyStats: MapInfo) => {
            console.log('MapComponent: Date statistice primite cu succes');
            
            // Proceseaza si combina datele
            if (countyStats && countyStats.regions) {
              this.countyOptions = countyStats.regions.map(region => ({
                code: region.code,
                name: region.name
              })).sort((a, b) => a.name.localeCompare(b.name));

              countyStats.regions.forEach((region: CountyData) => {
                const csvData = votingStats[region.code] || {};
                
                this.countyData[region.code] = {
                  ...region,
                  registeredVoters: csvData.registeredVoters || 0,
                  pollingStationCount: csvData.pollingStationCount || 0,
                  permanentListVoters: csvData.permanentListVoters || 0,
                  supplementaryListVoters: csvData.supplementaryListVoters || 0,
                  specialCircumstancesVoters: csvData.specialCircumstancesVoters || 0,
                  mobileUrnsVoters: csvData.mobileUrnsVoters || 0,
                  totalVoters: csvData.totalVoters || 0,
                  turnoutPercentage: csvData.turnoutPercentage || '0.00'
                };
              });
            }
            console.log('Voting Stats from CSV:', votingStats);
            console.log('Combined County Data:', this.countyData);
            
            this.isLoading = false;
            
            // Initializeaza harta
            setTimeout(() => {
              this.initializeMap();
            }, 100);
          },
          error: (error: any) => {
            console.error('MapComponent: Eroare la încărcarea datelor statistice:', error);
            this.isLoading = false;
          }
        });
      }).catch((error: any) => {
        console.error('MapComponent: Eroare la încărcarea GeoJSON:', error);
        this.isLoading = false;
      });
    },
    error: (error: any) => {
      console.error('MapComponent: Eroare la încărcarea datelor CSV:', error);
      
      // Continua incarcarea altor date chiar daca CSV esueaza
      this.loadGeoJsonData().then(geoData => {
        this.geoJsonData = geoData;
        this.mapService.getMapInfo().subscribe({
          next: (countyStats: MapInfo) => {
            if (countyStats && countyStats.regions) {
              countyStats.regions.forEach((region: CountyData) => {
                this.countyData[region.code] = region;
              });
            }
            this.isLoading = false;
            setTimeout(() => this.initializeMap(), 100);
          },
          error: (err) => {
            console.error('Eroare la încărcarea datelor statistice:', err);
            this.isLoading = false;
          }
        });
      }).catch(err => {
        console.error('Eroare la încărcarea GeoJSON:', err);
        this.isLoading = false;
      });
    }
  });
}
  initializeMapSettings(): void {
    // Asigură-te că efectul vizual corect este aplicat în funcție de valoarea relativeTo
    if (this.highlightField === 'prezenta') {
      // Aplică efectul de overlay corespunzător setării curente
      this.applyRelativeToEffect();
      
      // Actualizează și maxima sliderului
      this.updateSliderMaxForTurnout();
    }
  }


  // Metoda optimizata pentru initializarea hartii
  initializeMap(): void {
    if (!this.geoJsonData || !this.mapContainer) return;
    
    this.ngZone.runOutsideAngular(() => {
      // Curata orice SVG existent
      const container = this.mapContainer.nativeElement;
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
      
      // Obtine dimensiunile containerului
      const width = container.clientWidth;
      const height = container.clientHeight || 500;
      
      // Creaza SVG cu proportii adecvate
      this.svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .attr('class', 'romania-map');
      
      // Creaza proiectia cu fitExtent pentru a asigura o adaptare mai buna
      this.projection = d3.geoMercator()
        .fitExtent([[20, 20], [width - 20, height - 20]], this.geoJsonData);
      
      // Create path generator
      this.path = d3.geoPath().projection(this.projection);
      
      // Comportamentul de zoom imbunatatit
      this.zoom = d3.zoom()
      .scaleExtent([0.3, 9]) // limitele de zoom
      .translateExtent([[0, 0], [width, height]]) // limitele de translatie
      .on('zoom', (event) => {
        // Actualizeaza transformarea curenta
        this.currentTransform = event.transform;
        this.g.attr('transform', event.transform);
        
        // Ajusteaza grosimea conturului in functie de zoom
        const strokeWidth = 0.5 / event.transform.k;
        this.g.selectAll('.county-path')
          .attr('stroke-width', strokeWidth);
          
        // Ajusteaza dimensiunea textului in functie de zoom
        const fontSize = 10 / event.transform.k;
        this.g.selectAll('.county-label')
          .attr('font-size', `${fontSize}px`);
        this.g.selectAll('.polling-station-count')
          .attr('font-size', `${fontSize}px`);
        this.g.selectAll('.voters-count')
          .attr('font-size', `${fontSize}px`);
      });
      
      // Aplica zoom-ul la SVG
      this.svg.call(this.zoom);
      
      // Creaza un grup pentru toate elementele hartii
      this.g = this.svg.append('g');
      
      // Desenează județele cu evenimente de hover corecte
      const countyPaths = this.g.selectAll('.county-path')
        .data(this.geoJsonData.features)
        .enter()
        .append('path')
        .attr('class', 'county-path')
        .attr('id', (d: GeoFeature) => this.getCountyCode(d))
        .attr('d', this.path)
        .attr('fill', (d: GeoFeature) => this.getCountyColor(this.getCountyCode(d)))
        .attr('stroke', '#fff')
        .attr('stroke-width', 0.5);
  
      // Atașează evenimentele separat pentru a te asigura că sunt adăugate corect
      countyPaths.on('mouseover', (event: any, d: GeoFeature) => {
        // Important: Folosește event.target și oprește propagarea
        event.stopPropagation();
        this.ngZone.run(() => this.handleCountyMouseOver(event, d));
      })
      .on('mousemove', (event: any) => {
        event.stopPropagation();
        this.ngZone.run(() => this.handleCountyMouseMove(event));
      })
      .on('mouseout', (event: any, d: GeoFeature) => {
        event.stopPropagation();
        this.ngZone.run(() => this.handleCountyMouseOut(event, d));
      })
      .on('click', (event: any, d: GeoFeature) => {
        event.stopPropagation();
        this.ngZone.run(() => this.handleCountyClick(d));
      });
      
      // Creaza un grup pentru fiecare etichetă pentru a putea poziționa mai bine textul
      const labelGroups = this.g.selectAll('.county-label-group')
        .data(this.geoJsonData.features)
        .enter()
        .append('g')
        .attr('class', 'county-label-group')
        .attr('transform', (d: GeoFeature) => {
          const centroid = this.path.centroid(d);
          return `translate(${centroid[0]}, ${centroid[1]})`;
        });
      
      // Adaugă codul județului (prima linie)
      labelGroups.append('text')
        .attr('class', 'county-label')
        .attr('y', (d: GeoFeature) => {
          // Ajustează poziția verticală bazată pe highlightField
          // Dacă este selectat "sectii" sau "votanti", codul județului va fi puțin mai sus
          return (this.highlightField === 'sectii' || this.highlightField === 'votanti') ? -5 : 0;
        })
        .attr('text-anchor', 'middle')
        .attr('alignment-baseline', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#fff')
        .attr('pointer-events', 'none')
        .text((d: GeoFeature) => this.getCountyCode(d));
      
      // Adaugă numărul de secții de votare (a doua linie)
      // Această etichetă este afișată doar când highlightField este 'sectii'
      labelGroups.append('text')
        .attr('class', 'polling-station-count')
        .attr('y', 5)
        .attr('text-anchor', 'middle')
        .attr('alignment-baseline', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#fff')
        .attr('pointer-events', 'none')
        .attr('opacity', this.highlightField === 'sectii' ? 1 : 0) // Ascunde textul dacă nu sunt selectate secțiile
        .text((d: GeoFeature) => {
          const countyCode = this.getCountyCode(d);
          const county = this.countyData[countyCode];
          return county && county.pollingStationCount ? county.pollingStationCount : '';
        });
        
      // Adaugă numărul de votanți (a doua linie)
      // Această etichetă este afișată doar când highlightField este 'votanti'
      labelGroups.append('text')
        .attr('class', 'voters-count')
        .attr('y', 5)
        .attr('text-anchor', 'middle')
        .attr('alignment-baseline', 'middle')
        .attr('font-size', '9px')
        .attr('fill', '#fff')
        .attr('pointer-events', 'none')
        .attr('opacity', this.highlightField === 'votanti' ? 1 : 0) // Ascunde textul dacă nu e selectat votanți
        .text((d: GeoFeature) => {
          const countyCode = this.getCountyCode(d);
          const county = this.countyData[countyCode];
          return county && county.totalVoters ? this.formatVotersNumber(county.totalVoters) : '';
        });
        
      // Trebuie să fie în interiorul ngZone.run() pentru că funcția va actualiza UI
      this.ngZone.run(() => {
        // Inițializează setările hărții pentru a aplica efectele vizuale corecte
        this.initializeMapSettings();
      });
    });
  }

loadActiveRoundData(): void {
  console.log('Încărcare date în timp real pentru turul activ');
  
  // Încarcă doar structura geografică
  this.loadGeoJsonData().then(geoData => {
    this.geoJsonData = geoData;
    
    // Obține statisticile de vot în timp real
    this.mapService.getActiveRoundVotingStatistics().subscribe({
      next: (votingStats: any) => {
        console.log('Date statistice în timp real primite cu succes:', votingStats);
        
        // Creează un obiect countyData cu datele primite
        const countyData: { [key: string]: CountyData } = {};
        
        // Convertim datele primite în formatul așteptat de componentă
        Object.keys(votingStats).forEach(countyCode => {
          const stats = votingStats[countyCode];
          
          countyData[countyCode] = {
            name: this.getCountyNameByCode(countyCode),
            code: countyCode,
            voters: stats.total_voters || 0,
            percentage: stats.turnoutPercentage ? parseFloat(stats.turnoutPercentage) / 100 : 0,
            registeredVoters: stats.registeredVoters || 0,
            pollingStationCount: stats.pollingStationCount || 0,
            permanentListVoters: stats.permanentListVoters || 0,
            supplementaryListVoters: stats.supplementaryListVoters || 0,
            specialCircumstancesVoters: stats.specialCircumstancesVoters || 0,
            mobileUrnsVoters: stats.mobileUrnsVoters || 0,
            totalVoters: stats.total_voters || 0,
            turnoutPercentage: stats.turnoutPercentage || '0.00'
          };
        });
        
        this.countyData = countyData;
        this.isLoading = false;
        
        // Calculăm totaluri pentru statistici globale
        this.updateGlobalStatsFromActiveData(countyData);
        
        // Inițializăm harta
        setTimeout(() => {
          this.initializeMap();
        }, 100);
      },
      error: (error: any) => {
        console.error('Eroare la încărcarea datelor în timp real:', error);
        this.isLoading = false;
        
        // Inițializăm harta cu date goale
        this.countyData = {};
        setTimeout(() => {
          this.initializeMap();
        }, 100);
      }
    });
  }).catch((error: any) => {
    console.error('Eroare la încărcarea GeoJSON:', error);
    this.isLoading = false;
  });
}
getCountyNameByCode(countyCode: string): string {
  const countyNames: {[key: string]: string} = {
    'AB': 'Alba', 'AR': 'Arad', 'AG': 'Argeș', 'BC': 'Bacău', 'BH': 'Bihor',
    'BN': 'Bistrița-Năsăud', 'BT': 'Botoșani', 'BV': 'Brașov', 'BR': 'Brăila',
    'B': 'București', 'BZ': 'Buzău', 'CS': 'Caraș-Severin', 'CL': 'Călărași',
    'CJ': 'Cluj', 'CT': 'Constanța', 'CV': 'Covasna', 'DB': 'Dâmbovița',
    'DJ': 'Dolj', 'GL': 'Galați', 'GR': 'Giurgiu', 'GJ': 'Gorj', 'HR': 'Harghita',
    'HD': 'Hunedoara', 'IL': 'Ialomița', 'IS': 'Iași', 'IF': 'Ilfov', 'MM': 'Maramureș',
    'MH': 'Mehedinți', 'MS': 'Mureș', 'NT': 'Neamț', 'OT': 'Olt', 'PH': 'Prahova',
    'SM': 'Satu Mare', 'SJ': 'Sălaj', 'SB': 'Sibiu', 'SV': 'Suceava', 'TR': 'Teleorman',
    'TM': 'Timiș', 'TL': 'Tulcea', 'VS': 'Vaslui', 'VL': 'Vâlcea', 'VN': 'Vrancea'
  };
  
  return countyNames[countyCode] || countyCode;
}

// Metodă pentru calcularea statisticilor globale din datele active
updateGlobalStatsFromActiveData(countyData: { [key: string]: CountyData }): void {
  let totalRegisteredVoters = 0;
  let totalVotersCount = 0;
  
  Object.values(countyData).forEach(county => {
    totalRegisteredVoters += county.registeredVoters || 0;
    totalVotersCount += county.totalVoters || 0;
  });
  
  this.totalVoters = totalVotersCount.toString();
  
  if (totalRegisteredVoters > 0) {
    const overallTurnout = (totalVotersCount / totalRegisteredVoters * 100);
    this.totalPercentage = overallTurnout.toFixed(2);
  } else {
    this.totalPercentage = "0.00";
  }
}


  // Metoda pentru redimensionarea hartii la redimensionarea ferestrei
// Metoda pentru redimensionarea hartii la redimensionarea ferestrei
resizeMap(): void {
  if (!this.svg || !this.mapContainer) return;
  
  this.ngZone.runOutsideAngular(() => {
    const container = this.mapContainer.nativeElement;
    const width = container.clientWidth;
    const height = container.clientHeight || 500;
    
    // Actualizează dimensiunile SVG-ului
    this.svg
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet');
    
    if (this.mapLocation === 'romania') {
      // Codul existent pentru România
      this.projection.fitExtent([[20, 20], [width - 20, height - 20]], this.geoJsonData);
      // Restul codului pentru România...
    } else {
      // Logică îmbunătățită pentru harta mondială
      // Recalculăm proiecția pentru dimensiunile noi
      this.projection = d3.geoMercator()
        .center([0, 30])
        .scale(width / 6.5)
        .translate([width / 2, height / 2]);
      
      // Actualizăm path-ul
      this.path = d3.geoPath().projection(this.projection);
      
      // Actualizăm path-urile pentru țări
      this.g.selectAll('.country-path')
        .attr('d', this.path);
      
      // Actualizăm poziția etichetelor
      this.g.selectAll('.country-label, .country-voters').each((d: any, i: number, nodes: any) => {
        const node = d3.select(nodes[i]);
        const countryCode = node.text().split(' ')[0]; // Extragem codul țării
        
        const feature = this.worldGeoJsonData.features.find((f: GeoFeature) => 
          this.getCountryCode(f) === countryCode
        );
        
        if (feature) {
          const centroid = this.path.centroid(feature);
          if (!isNaN(centroid[0]) && !isNaN(centroid[1])) {
            node.attr('x', centroid[0]);
            node.attr('y', centroid[1] + (node.classed('country-voters') ? 12 : 0));
          }
        }
      });
      
      // Reaplicăm nivelul de zoom curent
      this.applyWorldMapZoom();
    }
  });
}
  
  
  // Determina codul judetului din feature
  getCountyCode(feature: GeoFeature): string {
    // Mapeaza numele judetului la codul judetului
    const countyCodeMap: {[key: string]: string} = {
      'Alba': 'AB', 'Arad': 'AR', 'Argeș': 'AG','Arges': 'AG', 'Bacău': 'BC','Bacau': 'BC', 'Bihor': 'BH',
      'Bistrița-Năsăud': 'BN','Bistrita-Nasaud': 'BN', 'Botoșani': 'BT','Botosani': 'BT', 'Brașov': 'BV','Brasov': 'BV', 'Brăila': 'BR','Braila': 'BR',
      'București': 'B','Bucuresti': 'B', 'Buzău': 'BZ','Buzau': 'BZ', 'Caraș-Severin': 'CS','Caras-Severin': 'CS', 'Călărași': 'CL','Calarasi': 'CL',
      'Cluj': 'CJ', 'Constanța': 'CT','Constanta': 'CT', 'Covasna': 'CV', 'Dâmbovița': 'DB','Dambovita': 'DB',
      'Dolj': 'DJ', 'Galați': 'GL', 'Galati': 'GL','Giurgiu': 'GR', 'Gorj': 'GJ', 'Harghita': 'HR',
      'Hunedoara': 'HD', 'Ialomița': 'IL','Ialomita': 'IL', 'Iași': 'IS','Iasi': 'IS', 'Ilfov': 'IF',
      'Maramureș': 'MM','Maramures': 'MM', 'Mehedinți': 'MH','Mehedinti': 'MH', 'Mureș': 'MS','Mures': 'MS', 'Neamț': 'NT','Neamt': 'NT',
      'Olt': 'OT', 'Prahova': 'PH', 'Satu Mare': 'SM', 'Sălaj': 'SJ','Salaj': 'SJ',
      'Sibiu': 'SB', 'Suceava': 'SV', 'Teleorman': 'TR', 'Timiș': 'TM','Timis': 'TM',
      'Tulcea': 'TL', 'Vaslui': 'VS', 'Vâlcea': 'VL', 'Valcea': 'VL','Vrancea': 'VN'
    };
    
    // Obtine numele judetului din proprietatile feature-ului
    const name = feature.properties.name;
    
    // Returneaza codul judetului sau numele daca nu este gasit
    return countyCodeMap[name] || name;
  }

  // Gestioneaza evenimentul de mouseover pentru un judet
  handleCountyMouseOver(event: any, feature: GeoFeature): void {
    console.log('Mouse over triggered for:', feature.properties.name);
    
    const countyCode = this.getCountyCode(feature);
    const countyData = this.countyData[countyCode];
    
    console.log('County data found:', countyData);
    
    // Verifică dacă avem date pentru județ
    if (countyData) {
      // Asigură-te că toate proprietățile necesare există în obiect
      this.hoveredCounty = {
        name: countyData.name || feature.properties.name,
        code: countyCode,
        voters: countyData.voters || 0,
        percentage: countyData.percentage || 0,
        
        // Adaugă explicit proprietățile din statistici
        registeredVoters: countyData.registeredVoters || 0,
        pollingStationCount: countyData.pollingStationCount || 0,
        permanentListVoters: countyData.permanentListVoters || 0,
        supplementaryListVoters: countyData.supplementaryListVoters || 0,
        specialCircumstancesVoters: countyData.specialCircumstancesVoters || 0,
        mobileUrnsVoters: countyData.mobileUrnsVoters || 0,
        totalVoters: countyData.totalVoters || 0,
        turnoutPercentage: countyData.turnoutPercentage !== undefined ? countyData.turnoutPercentage : 0
      };
    } else {
      // Dacă nu avem date, folosește un obiect gol cu valori implicite
      this.hoveredCounty = {
        name: feature.properties.name,
        code: countyCode,
        voters: 0,
        percentage: 0,
        registeredVoters: 0,
        pollingStationCount: 0,
        permanentListVoters: 0,
        supplementaryListVoters: 0,
        specialCircumstancesVoters: 0,
        mobileUrnsVoters: 0,
        totalVoters: 0,
        turnoutPercentage: 0
      };
    }
    
    console.log('Set hoveredCounty to:', this.hoveredCounty);
    
    // Forțează detectarea schimbărilor
    this.ngZone.run(() => {});
    
    // Calculează poziția corectă a tooltip-ului 
    const mapRect = this.mapContainer.nativeElement.getBoundingClientRect();
    const x = event.pageX - mapRect.left;
    const y = event.pageY - mapRect.top;
    
    // Setează poziția tooltip-ului
    const tooltipWidth = 280; // Lățime aproximativă tooltip
    const tooltipHeight = 250; // Înălțime aproximativă tooltip
    
    let posX = x;
    let posY = y;
    
    // Ajustare orizontală - previne ieșirea din dreapta
    if (x + tooltipWidth > mapRect.width) {
      posX = x - tooltipWidth;
    }
    
    // Ajustare verticală - previne ieșirea din jos
    if (y + tooltipHeight > mapRect.height) {
      posY = y - tooltipHeight;
    }
    
    // Asigură-te că tooltip-ul nu iese din stânga sau sus
    posX = Math.max(10, posX);
    posY = Math.max(10, posY);
    
    this.hoverPosition = {
      x: posX,
      y: posY
    };
    
    console.log('Set hoverPosition to:', this.hoverPosition);
    
    // Schimbă culoarea județelor
    d3.select(event.target).attr('fill', '#0066cc');
  }
  // Gestioneaza miscarea mouse ului peste un judet
  handleCountyMouseMove(event: any): void {
    if (!this.hoveredCounty) return; // Ieși dacă nu avem un județ hover
    
    // Calculează poziția tooltip-ului în interiorul containerului hărții
    const mapRect = this.mapContainer.nativeElement.getBoundingClientRect();
    const x = event.clientX - mapRect.left;
    const y = event.clientY - mapRect.top;
    
    // Verifică marginile pentru a ne asigura că tooltip-ul rămâne în container
    const tooltipWidth = 280;
    const tooltipHeight = 250;
    
    let posX = x;
    let posY = y;
    
    // Ajustare orizontală - previne ieșirea din dreapta
    if (x + tooltipWidth > mapRect.width) {
      posX = x - tooltipWidth;
    }
    
    // Ajustare verticală - previne ieșirea din jos
    if (y + tooltipHeight > mapRect.height) {
      posY = y - tooltipHeight;
    }
    
    // Asigură-te că tooltip-ul nu iese din stânga sau sus
    posX = Math.max(10, posX);
    posY = Math.max(10, posY);
    
    this.hoverPosition = {
      x: posX,
      y: posY
    };
  }
  
  
  // Gestioneaza iesirea mouse-ului de pe un judet
  handleCountyMouseOut(event: any, feature: GeoFeature): void {
    const countyCode = this.getCountyCode(feature);
    
    // Resetează culoarea județului
    d3.select(event.target as SVGPathElement)
      .attr('fill', this.getCountyColor(countyCode));
    
    // Șterge județul hover
    this.hoveredCounty = null;
  }
  // Gestioneaza click-ul pe un judet
// Gestionează click-ul pe un județ
handleCountyClick(feature: GeoFeature): void {
  const countyCode = this.getCountyCode(feature);
  console.log(`Județ selectat: ${feature.properties.name} (${countyCode})`);
  
  // Verifică dacă turul curent are date
  if (!this.currentRoundState.hasData) {
    // Pentru tururi fără date, afișăm un mesaj informativ
    alert(`Nu există date disponibile pentru UAT-urile din județul ${feature.properties.name} în ${this.currentRoundState.roundId}.`);
    return;
  }
  
  // Opțional: întreabă utilizatorul dacă dorește să vadă UAT-urile pentru acest județ
  if (confirm(`Doriți să vizualizați UAT-urile pentru județul ${feature.properties.name}?`)) {
    // Setăm flag-ul pentru a sări peste încărcarea hărții de județe
    this.skipCountyMapLoad = true;
    
    // Încărcăm direct harta UAT
    this.loadCountyUATMap(countyCode);
  } else {
    // Altfel, doar zoom pe județ (codul existent)
    if (this.svg && this.path) {
      const bounds = this.path.bounds(feature);
      const dx = bounds[1][0] - bounds[0][0];
      const dy = bounds[1][1] - bounds[0][1];
      const x = (bounds[0][0] + bounds[1][0]) / 2;
      const y = (bounds[0][1] + bounds[1][1]) / 2;
      
      const container = this.mapContainer.nativeElement;
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      // Calculează scara și translația pentru zoom
      const scale = Math.min(5, 0.9 / Math.max(dx / width, dy / height));
      const translate = [width / 2 - scale * x, height / 2 - scale * y];
      
      // Aplică transformarea pentru zoom
      this.svg.transition()
        .duration(750)
        .call(this.zoom.transform, d3.zoomIdentity
          .translate(translate[0], translate[1])
          .scale(scale));
    }
  }
}
  
  // Metoda pentru a incarca datele GeoJSON
  private loadGeoJsonData(): Promise<any> {
    return new Promise((resolve, reject) => {
      // Foloseste fetch API pentru a incarca fisierul GeoJSON
      fetch('assets/maps/romania.geojson')
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => resolve(data))
        .catch(error => reject(error));
    });
  }
  
  // Determina culoarea judetului in functie de date
// Determina culoarea judetului in functie de date și modul de vizualizare
getCountyColor(countyCode: string): string {
  const county = this.countyData[countyCode];
  if (!county) return '#d0d0ff'; // Culoare implicită pentru județe fără date
  
  // Verifică dacă suntem în modul "secții de votare"
  if (this.highlightField === 'sectii') {
    // În modul secții, folosim pollingStationCount pentru filtrare
    const stationCount = county.pollingStationCount || 0;
    
    // Dacă numărul de secții este exact ca valoarea sliderului sau este valoarea maximă când slider-ul e la maxim
    if (stationCount === this.filterPercentage || 
        (stationCount === parseInt(this.maxValue) && this.filterPercentage === parseInt(this.maxValue))) {
      // Evidențiem acest județ cu o culoare contrastantă
      return '#1f1f1f'; // Culoare contrastantă pentru județele la pragul de filtrare
    } else if (stationCount > this.filterPercentage) {
      // Pentru celelalte județe, folosim schema de culori normală, dar bazată pe numărul de secții
      // Calculăm un procentaj bazat pe numărul de secții raportat la numărul maxim de secții
      let maxStations = 0;
      Object.values(this.countyData).forEach(c => {
        if (c.pollingStationCount && c.pollingStationCount > maxStations) {
          maxStations = c.pollingStationCount;
        }
      });
      
      const normalizedPercentage = maxStations > 0 ? stationCount / maxStations : 0;
      
      if (normalizedPercentage > 0.6) return '#4050e0';
      if (normalizedPercentage > 0.4) return '#6070e0';
      if (normalizedPercentage > 0.2) return '#8090e0';
      if (normalizedPercentage > 0.1) return '#a0b0e0';
      return '#c0d0ff';
    } else {
      // Județe care au mai puține secții decât filtrul
      return 'rgba(255, 255, 255, 0.1)'; // Culoare foarte transparentă
    }
  }
  else if (this.highlightField === 'votanti') {
    // În modul votanți, folosim totalVoters pentru filtrare
    const totalVoters = county.totalVoters || 0;
    
    // Dacă numărul de votanți este mai mare sau egal cu valoarea sliderului
    if (totalVoters >= this.filterPercentage) {
      // Evidențiem acest județ cu o culoare contrastantă
      return '#1f1f1f'; // Culoare contrastantă pentru județele peste pragul de filtrare
    }
    
    // Pentru celelalte județe, folosim schema de culori normală, dar bazată pe numărul de votanți
    // Calculăm un procentaj bazat pe numărul de votanți raportat la numărul maxim de votanți
    let maxVoters = 0;
    Object.values(this.countyData).forEach(c => {
      if (c.totalVoters && c.totalVoters > maxVoters) {
        maxVoters = c.totalVoters;
      }
    });
    
    const normalizedPercentage = maxVoters > 0 ? totalVoters / maxVoters : 0;
    
    if (normalizedPercentage > 0.6) return '#4050e0';
    if (normalizedPercentage > 0.4) return '#6070e0';
    if (normalizedPercentage > 0.2) return '#8090e0';
    if (normalizedPercentage > 0.1) return '#a0b0e0';
    return '#c0d0ff';
  }
  else if (this.highlightField === 'prezenta') {
    // Pentru prezență la vot folosim turnoutPercentage
    let turnoutValue = 0;
    if (typeof county.turnoutPercentage === 'string') {
      turnoutValue = parseFloat(county.turnoutPercentage);
    } else {
      turnoutValue = county.turnoutPercentage as number;
    }
    
    // Dacă procentajul județului este foarte aproape de valoarea slider-ului (toleranță de 0.1%)
    if (Math.abs(turnoutValue - this.filterPercentage) < 0.1) {
      // Evidențiază județele care se potrivesc exact cu filtrul
      return '#1f1f1f'; // Culoare contrastantă pentru județele la pragul de filtrare
    }
    
    // Pentru toate celelalte judete, foloseste schema de culori în funcție de relativeTo
    const percentage = county.percentage;
    
    // Verifică dacă este selectat modul "100%" (relativeTo === 'total')
    if (this.relativeTo === 'total') {
      // Culori mai închise pentru modul "100%"
      if (percentage > 0.6) return '#303dcc'; // Albastru mai închis
      if (percentage > 0.4) return '#4050c0'; // Albastru mai închis
      if (percentage > 0.2) return '#5060c0'; // Albastru mai închis
      if (percentage > 0.1) return '#6080c0'; // Albastru mai închis
      return '#a0b0e0'; // Albastru mai închis pentru restul județelor
    } else {
      // Schema de culori originală pentru modul "Maxim"
      if (percentage > 0.6) return '#4050e0';
      if (percentage > 0.4) return '#6070e0';
      if (percentage > 0.2) return '#8090e0';
      if (percentage > 0.1) return '#a0b0e0';
      return '#c0d0ff';
    }
  } 
  else {
    // Pentru alte moduri, folosim exact schema originală
    const percentage = county.percentage;
    if (percentage > 0.6) return '#4050e0';
    if (percentage > 0.4) return '#6070e0';
    if (percentage > 0.2) return '#8090e0';
    if (percentage > 0.1) return '#a0b0e0';
    return '#c0d0ff';
  }
}
// Metoda pentru actualizarea filtrului
onFilterChange(): void {
  // Actualizează culorile județelor/țărilor pe baza noului filtru
  if (this.mapLocation === 'strainatate') {
    if (this.g) {
      this.g.selectAll('.country-path')
        .attr('fill', (d: GeoFeature) => this.getCountryColor(this.getCountryCode(d)));
    }
  } else {
    if (this.g) {
      this.g.selectAll('.county-path')
        .attr('fill', (d: GeoFeature) => this.getCountyColor(this.getCountyCode(d)));
    }
  }
  
  // Actualizează statisticile globale
  this.updateGlobalStats();
  
  // Actualizează textul de filtrare
  this.updateFilterText();
}
// Metoda pentru actualizarea statisticilor globale
updateGlobalStats(): void {
  if (this.highlightField === 'sectii') {
    let countriesOrCountiesWithExactCount = 0;
    let totalEntities = 0;
    let totalStations = 0;
    
    if (this.mapLocation === 'strainatate') {
      Object.values(this.countryData).forEach(country => {
        if (!country.pollingStationCount) return;
        
        totalEntities++;
        const stationCount = country.pollingStationCount || 0;
        totalStations += stationCount;
        
        if (stationCount === this.filterPercentage || 
            (stationCount === parseInt(this.maxValue) && this.filterPercentage === parseInt(this.maxValue))) {
          countriesOrCountiesWithExactCount++;
        }
      });
    } else {
      Object.values(this.countyData).forEach(county => {
        totalEntities++;
        const stationCount = county.pollingStationCount || 0;
        totalStations += stationCount;
        
        if (stationCount === this.filterPercentage || 
            (stationCount === parseInt(this.maxValue) && this.filterPercentage === parseInt(this.maxValue))) {
          countriesOrCountiesWithExactCount++;
        }
      });
    }
    
    this.totalVoters = countriesOrCountiesWithExactCount.toString();
    
    if (totalEntities > 0) {
      this.totalPercentage = (countriesOrCountiesWithExactCount / totalEntities * 100).toFixed(2);
    } else {
      this.totalPercentage = "0.00";
    }
    
    console.log(`Entități cu exact ${this.filterPercentage} secții: ${countriesOrCountiesWithExactCount}`);
  } else if (this.highlightField === 'votanti') {
    if (this.mapLocation === 'strainatate') {
      let countriesWithExactVoters = 0;
      let totalCountries = 0;
      let totalVotersSum = 0;
      
      Object.values(this.countryData).forEach(country => {
        if (!country.totalVoters) return;
        
        totalCountries++;
        const voters = country.totalVoters || 0;
        totalVotersSum += voters;
        
        if (voters === this.filterPercentage || 
            (voters === parseInt(this.maxValue) && this.filterPercentage === parseInt(this.maxValue))) {
          countriesWithExactVoters++;
        }
      });
      
      this.totalVoters = countriesWithExactVoters.toString();
      
      if (totalCountries > 0) {
        this.totalPercentage = (countriesWithExactVoters / totalCountries * 100).toFixed(2);
      } else {
        this.totalPercentage = "0.00";
      }
    } else {
      let countiesAboveThreshold = 0;
      let totalCounties = 0;
      let totalVotersSum = 0;
      
      Object.values(this.countyData).forEach(county => {
        totalCounties++;
        const voters = county.totalVoters || 0;
        totalVotersSum += voters;
        
        if (voters >= this.filterPercentage) {
          countiesAboveThreshold++;
        }
      });
      
      this.totalVoters = countiesAboveThreshold.toString();
      this.totalPercentage = (countiesAboveThreshold / totalCounties * 100).toFixed(2);
      
      console.log(`Entități cu cel puțin ${this.filterPercentage} votanți: ${countiesAboveThreshold}`);
    }
  } else {
    if (this.mapLocation === 'strainatate') {
      this.totalPercentage = this.filterPercentage.toFixed(2);
      this.totalVoters = "0";
    } else {
      let countiesAtThreshold = 0;
      let totalCounties = 0;
      
      Object.values(this.countyData).forEach(county => {
        totalCounties++;
        
        if (this.highlightField === 'prezenta') {
          let turnoutValue = 0;
          if (typeof county.turnoutPercentage === 'string') {
            turnoutValue = parseFloat(county.turnoutPercentage);
          } else {
            turnoutValue = county.turnoutPercentage as number;
          }
          
          if (Math.abs(turnoutValue - this.filterPercentage) < 0.1) {
            countiesAtThreshold++;
          }
        } else {
          if (Math.abs(county.percentage * 100 - this.filterPercentage) < 0.1) {
            countiesAtThreshold++;
          }
        }
      });

      this.totalPercentage = this.filterPercentage.toFixed(2);
      this.totalVoters = countiesAtThreshold.toString();
      
      console.log(`Județe cu prezență de ${this.filterPercentage}%: ${countiesAtThreshold}`);
    }
  }
}

   // Metode de control pentru filtre
   setMapLevel(level: string): void {
    if (this.mapLevel === level) return;
    
    this.mapLevel = level;
    console.log(`Nivel hartă setat la: ${level}`);
    
    if (level === 'uaturi') {
      // Încarcă automat primul județ din listă dacă există
      if (this.countyOptions && this.countyOptions.length > 0) {
        const firstCounty = this.countyOptions[0];
        this.loadCountyUATMap(firstCounty.code);
      } else {
        console.log('Niciun județ disponibil pentru încărcare automată');
      }
    } else {
      // Revino la harta de județe
      this.isUATView = false;
      this.selectedCounty = null;
      this.initializeMap();
    }
  }
// În map.component.ts
loadCountyUATMap(countyCode: string): void {
  if (!countyCode) return;
  
  console.log('Încărcare hartă UAT pentru județul:', countyCode);
  
  // Actualizează URL-ul pentru a reflecta starea UAT
  const currentParams: {[key: string]: any} = { ...this.route.snapshot.queryParams };
  
  // Adăugăm sau actualizăm parametrii UAT
  currentParams['uatView'] = 'true';
  currentParams['county'] = countyCode;
  
  // Actualizăm URL-ul fără a reîncărca componenta
  this.router.navigate([], {
    relativeTo: this.route,
    queryParams: currentParams,
    replaceUrl: true // înlocuiește URL-ul actual în istoric
  });
  
  // Setează starea componentei
  this.isLoading = true;
  this.selectedCounty = countyCode;
  this.isUATView = true;
  this.mapLevel = 'uaturi';
  
  // Obține datele GeoJSON pentru UAT
  this.mapService.getCountyUATGeoJson(countyCode).subscribe({
    next: (geoData) => {
      if (!geoData) {
        console.error(`Nu există date GeoJSON disponibile pentru județul ${countyCode}`);
        this.isLoading = false;
        return;
      }
      
      this.uatGeoJsonData = geoData;
      console.log('Date GeoJSON pentru UAT:', this.uatGeoJsonData);
      
      // Oprește loading înainte de inițializarea hărții
      this.isLoading = false;
      
      // Inițializăm imediat harta UAT
      if (this.mapContainer) {
        this.initializeUATMap();
      } else {
        console.error('Container hartă (mapContainer) nu este disponibil');
      }
      
      // Actualizează selectorul de județe (dacă există) după ce harta este inițializată
      setTimeout(() => {
        const countySelector = document.getElementById('county-select') as HTMLSelectElement;
        if (countySelector) {
          countySelector.value = countyCode;
        }
      }, 100);
    },
    error: (error) => {
      console.error(`Eroare la încărcarea UAT map pentru județul ${countyCode}:`, error);
      this.isLoading = false;
    }
  });
}

initializeUATMap(): void {
  console.log('mapContainer:', this.mapContainer);
  console.log('uatGeoJsonData:', this.uatGeoJsonData);
  
  if (!this.uatGeoJsonData) {
    console.error('Date GeoJSON lipsă');
    return;
  }
  
  if (!this.mapContainer) {
    console.error('Container hartă lipsă');
    return;
  }
  
  console.log('Începe inițializarea hărții UAT');
  
  this.ngZone.runOutsideAngular(() => {
    // Curăță containerul
    const container = this.mapContainer.nativeElement;
    console.log('Container dimensiuni:', container.clientWidth, 'x', container.clientHeight);
    
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    
    // Dimensiuni adaptate la container
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;
    
    // Creează SVG
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .style('background-color', '#1a1a1a')
      .style('border', 'none')
      .style('display', 'block')
      .style('max-width', '100%')
      .style('max-height', '100%')
      .style('margin', '0');
    
    // Creează grupul pentru hartă
    const g = svg.append('g');
    
    // Salvează referințele
    this.svg = svg;
    this.g = g;
    
    try {
      // Creează proiecția
      this.projection = d3.geoMercator()
        .fitExtent([[20, 20], [width - 20, height - 20]], this.uatGeoJsonData);
      
      this.path = d3.geoPath().projection(this.projection);
      
      // Configurează zoom-ul
      this.zoom = d3.zoom()
        .scaleExtent([0.3, 9])
        .on('zoom', (event) => {
          g.attr('transform', `translate(${event.transform.x},${event.transform.y}) scale(${event.transform.k})`);
          
          const strokeWidth = 0.5 / event.transform.k;
          g.selectAll('.uat-path')
            .attr('stroke-width', strokeWidth);
        });
      
      // Aplică zoom
      svg.call(this.zoom);
      
      // Desenează UAT-urile
      const paths = g.selectAll('.uat-path')
        .data(this.uatGeoJsonData.features)
        .enter()
        .append('path')
        .attr('class', 'uat-path')
        .attr('d', this.path)
        .attr('fill', () => {
          // Setează o culoare mai deschisă pentru tururile fără date
          return this.currentRoundState.hasData ? '#80a0e0' : '#555555';
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 0.5);
      
      console.log('Număr de path-uri create:', paths.size());
      
      // Adaugă evenimente de hover doar dacă turul actual are date
      if (this.currentRoundState.hasData) {
        paths.on('mouseover', (event, d: any) => {
          this.ngZone.run(() => {
            
            d3.select(event.target)
              .attr('fill', '#0066cc');
            
            // Actualizează tooltip
            this.hoveredCounty = {
              name: d.properties.name,
              code: this.selectedCounty || '',
              voters: 0,
              percentage: 0,
              registeredVoters: 0,
              pollingStationCount: 0,
              permanentListVoters: 0,
              supplementaryListVoters: 0,
              specialCircumstancesVoters: 0,
              mobileUrnsVoters: 0,
              totalVoters: 0,
              turnoutPercentage: 0
            };
            
            // Poziționează tooltip
            const mapRect = this.mapContainer.nativeElement.getBoundingClientRect();
            this.hoverPosition = {
              x: event.pageX - mapRect.left,
              y: event.pageY - mapRect.top
            };
          });
        })
        .on('mouseout', (event) => {
          this.ngZone.run(() => {
            d3.select(event.target)
              .attr('fill', '#80a0e0');
            
            this.hoveredCounty = null;
          });
        });
      } else {
        // Adaugă o notificare vizuală pentru tururile fără date
        svg.append('text')
          .attr('x', width / 2)
          .attr('y', height / 2)
          .attr('text-anchor', 'middle')
          .attr('fill', 'white')
          .attr('font-size', '16px')
          .text(`Nu există date disponibile pentru ${this.currentRoundState.roundId}`);
      }

      // Adaugă întotdeauna un titlu/antet pentru a identifica județul, indiferent de existența datelor
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', 25)
        .attr('text-anchor', 'middle')
        .attr('fill', 'white')
        .attr('font-size', '18px')
        .attr('font-weight', 'bold')
        .text(`UAT-uri ${this.getCountyName(this.selectedCounty || '')}`);
      
    } catch (error: any) {
      console.error('Eroare în procesarea sau desenarea GeoJSON:', error);
      
      // Afișează eroarea
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', 'red')
        .attr('font-size', '16px')
        .text(`Eroare: ${error.message}`);
    }
  });
  
  console.log('Finalizare inițializare hartă UAT');
}
  
  // Metodă pentru revenirea la vizualizarea județelor
backToCountyView(): void {
  this.mapLevel = 'judete';
  this.isUATView = false;
  this.selectedCounty = null;
  
  // Actualizează URL-ul pentru a elimina parametrii UAT
  const currentParams: {[key: string]: any} = { ...this.route.snapshot.queryParams };
  
  // Elimină parametrii UAT folosind accesarea corectă prin index
  if (currentParams['uatView']) {
    delete currentParams['uatView'];
  }
  
  if (currentParams['county']) {
    delete currentParams['county'];
  }
  
  // Actualizăm URL-ul fără a reîncărca componenta
  this.router.navigate([], {
    relativeTo: this.route,
    queryParams: currentParams,
    replaceUrl: true // înlocuiește URL-ul actual în istoric
  });
  
  // Inițializează harta județelor
  setTimeout(() => {
    this.initializeMap();
  }, 100);
}
// Metoda pentru a obține numele unui județ după codul său
getCountyName(countyCode: string): string {
  const county = Object.values(this.countyData).find(c => c.code === countyCode);
  return county ? county.name : countyCode;
}

  showCountySelectionDialog(): void {
    // Implementată în HTML ca un dropdown sau dialog modal
    console.log('Afișează selector județe pentru vizualizare UAT');
  }
  
  setHighlightField(field: string): void {
    const previousField = this.highlightField;
    this.highlightField = field;
    
    console.log(`Câmp evidențiere schimbat la: ${field}`);
    
    if (this.mapLocation === 'strainatate' && this.g) {
      this.addCountryLabels();
      
      this.g.selectAll('.country-path')
        .attr('fill', (d: GeoFeature) => this.getCountryColor(this.getCountryCode(d)));
    }
    
    if (field === 'sectii') {
      let minPollingStations = 0;
      let maxPollingStations = 0;
      
      if (this.mapLocation === 'strainatate') {
        Object.values(this.countryData).forEach(country => {
          const stationCount = Number(country.pollingStationCount || 0);
          if (stationCount > maxPollingStations) maxPollingStations = stationCount;
        });
        
        console.log(`Valoare minimă secții străinătate: ${minPollingStations}, Valoare maximă secții străinătate: ${maxPollingStations}`);
      } else {
        Object.values(this.countyData).forEach(county => {
          const stationCount = Number(county.pollingStationCount || 0);
          if (stationCount > maxPollingStations) maxPollingStations = stationCount;
        });
        
        console.log(`Valoare minimă secții județe: ${minPollingStations}, Valoare maximă secții județe: ${maxPollingStations}`);
      }
      
      if (maxPollingStations < 1) {
        maxPollingStations = 1;
      }
      
      this.minValue = minPollingStations.toString();
      this.maxValue = maxPollingStations.toString();
      
      this.filterPercentage = minPollingStations;
      
      setTimeout(() => {
        const slider = document.querySelector('.percentage-slider') as HTMLInputElement;
        if (slider) {
          slider.min = minPollingStations.toString();
          slider.max = maxPollingStations.toString();
          slider.value = minPollingStations.toString();
          slider.step = '1';
          
          console.log(`Slider configurat cu min: ${slider.min}, max: ${slider.max}, valoare: ${slider.value}`);
        }
        
        const minLabel = document.querySelector('.min-label span');
        const maxLabel = document.querySelector('.max-label span');
        if (minLabel) minLabel.textContent = minPollingStations.toString();
        if (maxLabel) maxLabel.textContent = maxPollingStations.toString();
      }, 0);
    } 
    else if (field === 'votanti') {
      if (this.mapLocation === 'strainatate') {
        let minVoters = 0;
        let maxVoters = 0;
        
        Object.values(this.countryData).forEach(country => {
          const totalVoters = Number(country.totalVoters || 0);
          if (totalVoters > maxVoters) maxVoters = totalVoters;
        });
        
        console.log(`Valoare minimă votanți străinătate: ${minVoters}, Valoare maximă votanți străinătate: ${maxVoters}`);
        
        this.minValue = minVoters.toString();
        this.maxValue = maxVoters.toString();
        
        this.filterPercentage = minVoters;
        
        setTimeout(() => {
          const slider = document.querySelector('.percentage-slider') as HTMLInputElement;
          if (slider) {
            slider.min = minVoters.toString();
            slider.max = maxVoters.toString();
            slider.value = minVoters.toString();
            slider.step = '100';
            
            console.log(`Slider configurat cu min: ${slider.min}, max: ${slider.max}, valoare: ${slider.value}`);
          }
          
          const minLabel = document.querySelector('.min-label span');
          const maxLabel = document.querySelector('.max-label span');
          if (minLabel) minLabel.textContent = minVoters.toString();
          if (maxLabel) maxLabel.textContent = maxVoters.toString();
        }, 0);
      } else {
        let minVoters = Number.MAX_VALUE;
        let maxVoters = 0;
        
        Object.values(this.countyData).forEach(county => {
          const totalVoters = Number(county.totalVoters || 0);
          
          if (totalVoters < minVoters) minVoters = totalVoters;
          if (totalVoters > maxVoters) maxVoters = totalVoters;
        });
        
        console.log(`Valoare minimă votanți: ${minVoters}, Valoare maximă votanți: ${maxVoters}`);
        
        if (maxVoters <= minVoters) {
          maxVoters = minVoters + 1;
        }
        
        minVoters = Math.floor(minVoters / 1000) * 1000;
        maxVoters = Math.ceil(maxVoters / 1000) * 1000;
        
        this.minValue = minVoters.toString();
        this.maxValue = maxVoters.toString();
        
        this.filterPercentage = minVoters;
        
        setTimeout(() => {
          const slider = document.querySelector('.percentage-slider') as HTMLInputElement;
          if (slider) {
            slider.min = minVoters.toString();
            slider.max = maxVoters.toString();
            slider.value = minVoters.toString();
            slider.step = '1000';
            
            console.log(`Slider configurat cu min: ${slider.min}, max: ${slider.max}, valoare: ${slider.value}`);
          }
          
          const minLabel = document.querySelector('.min-label span');
          const maxLabel = document.querySelector('.max-label span');
          if (minLabel) minLabel.textContent = minVoters.toLocaleString();
          if (maxLabel) maxLabel.textContent = maxVoters.toLocaleString();
        }, 0);
      }
    }
    else {
      this.minValue = '0';
      this.maxValue = '100';
      this.filterPercentage = 0;
      
      if (field === 'prezenta') {
        this.applyRelativeToEffect();
      }
      
      setTimeout(() => {
        const slider = document.querySelector('.percentage-slider') as HTMLInputElement;
        if (slider) {
          slider.min = '0';
          slider.max = '100';
          slider.value = '0';
          slider.step = '0.1';
        }
        
        const minLabel = document.querySelector('.min-label span');
        const maxLabel = document.querySelector('.max-label span');
        if (minLabel) minLabel.textContent = '0';
        if (maxLabel) maxLabel.textContent = '100';
        
        if (field === 'prezenta') {
          this.updateSliderMaxForTurnout();
        }
      }, 0);
    }
    
    if (this.g) {
      if (this.mapLocation === 'romania') {
        this.g.selectAll('.county-path')
          .attr('fill', (d: GeoFeature) => this.getCountyColor(this.getCountyCode(d)));
          
        if (previousField !== field && (previousField === 'sectii' || field === 'sectii')) {
          this.g.selectAll('.county-label')
            .transition()
            .duration(300)
            .attr('y', field === 'sectii' ? -5 : 0);
          
          this.g.selectAll('.polling-station-count')
            .transition()
            .duration(300)
            .attr('opacity', field === 'sectii' ? 1 : 0);
        }
        
        if (previousField !== field && (previousField === 'votanti' || field === 'votanti')) {
          let votersLabels = this.g.selectAll('.voters-count');
          
          if (field === 'votanti') {
            if (votersLabels.empty()) {
              this.g.selectAll('.county-label-group')
                .append('text')
                .attr('class', 'voters-count')
                .attr('y', 7)
                .attr('text-anchor', 'middle')
                .attr('alignment-baseline', 'middle')
                .attr('font-size', '9px')
                .attr('fill', '#fff')
                .attr('pointer-events', 'none')
                .attr('opacity', 0)
                .text((d: GeoFeature) => {
                  const countyCode = this.getCountyCode(d);
                  const county = this.countyData[countyCode];
                  if (county && county.totalVoters) {
                    return this.formatVotersNumber(county.totalVoters);
                  }
                  return '';
                });
            }
            
            this.g.selectAll('.voters-count')
              .transition()
              .duration(300)
              .attr('opacity', 1);
              
            this.g.selectAll('.county-label')
              .transition()
              .duration(300)
              .attr('y', -5);
          } else {
            this.g.selectAll('.voters-count')
              .transition()
              .duration(300)
              .attr('opacity', 0);
              
            if (field !== 'sectii') {
              this.g.selectAll('.county-label')
                .transition()
                .duration(300)
                .attr('y', 0);
            }
          }
        }
      }
    }
    
    this.updateFilterText();
  }

  // Funcție utilitară pentru formatarea numărului de votanți
  formatVotersNumber(value: number): string {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(0) + 'k';
    }
    return value.toString();
  }
  
  updateFilterText(): void {
    setTimeout(() => {
      const filterValueElement = document.querySelector('.filter-value span');
      if (filterValueElement) {
        if (this.highlightField === 'sectii') {
          filterValueElement.textContent = `Filtrare: ${Math.round(this.filterPercentage)} secții`;
        } else if (this.highlightField === 'votanti') {
          if (this.mapLocation === 'strainatate') {
            filterValueElement.textContent = `Filtrare: ${this.filterPercentage} votanți`;
          } else {
            filterValueElement.textContent = `Filtrare: ${this.filterPercentage.toLocaleString()} votanți`;
          }
        } else {
          filterValueElement.textContent = `Filtrare: ${this.filterPercentage.toFixed(1)}%`;
        }
      }
    }, 0);
  }
  applyRelativeToEffect(): void {
    // Verificăm să avem un SVG valid
    if (!this.svg) return;
    
    // Selectăm overlayul existent sau îl creăm dacă nu există
    let overlay = this.svg.select('.map-overlay');
    const container = this.mapContainer.nativeElement;
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    if (overlay.empty()) {
      overlay = this.svg.append('rect')
        .attr('class', 'map-overlay')
        .attr('width', width)
        .attr('height', height)
        .attr('fill', 'rgba(0, 0, 0, 0.15)')
        .attr('opacity', 0)
        .attr('pointer-events', 'none'); // IMPORTANT: Adaugă această linie pentru a permite evenimente mouse
    }
    
    // Aplicăm efectul de overlay
    if (this.relativeTo === 'total') {
      overlay.transition()
        .duration(300)
        .attr('opacity', 1);
    } else {
      overlay.transition()
        .duration(300)
        .attr('opacity', 0);
    }
  }
  
  // Funcție nouă pentru a actualiza maxima sliderului în funcție de relativeTo
  updateSliderMaxForTurnout(): void {
    if (this.highlightField !== 'prezenta') return;
    
    setTimeout(() => {
      const slider = document.querySelector('.percentage-slider') as HTMLInputElement;
      const maxLabel = document.querySelector('.max-label span');
      
      if (this.relativeTo === 'total') {
        // Pentru 100%, maxima este întotdeauna 100
        if (slider) slider.max = '100';
        if (maxLabel) maxLabel.textContent = '100';
      } else {
        // Pentru 'maxim', găsește valoarea maximă de prezență la vot
        let maxTurnout = 0;
        Object.values(this.countyData).forEach(county => {
          let turnoutValue = 0;
          if (typeof county.turnoutPercentage === 'string') {
            turnoutValue = parseFloat(county.turnoutPercentage);
          } else {
            turnoutValue = county.turnoutPercentage as number;
          }
          
          if (turnoutValue > maxTurnout) maxTurnout = turnoutValue;
        });
        
        // Aplicăm valoarea găsită
        if (slider) slider.max = maxTurnout.toString();
        if (maxLabel) maxLabel.textContent = maxTurnout.toFixed(2);
      }
    }, 0);
  }
  setRelativeTo(relativeTo: string): void {
    this.relativeTo = relativeTo;
    
    // Actualizează vizualizarea în funcție de modul selectat
    if (this.highlightField === 'prezenta') {
      // Aplicăm efectul vizual (overlay) în funcție de relativeTo
      this.applyRelativeToEffect();
      
      // Actualizează maxima sliderului în funcție de relativeTo
      this.updateSliderMaxForTurnout();
    }
    
    // Actualizează vizualizarea
    if (this.g) {
      this.g.selectAll('.county-path')
        .attr('fill', (d: GeoFeature) => this.getCountyColor(this.getCountyCode(d)));
    }
    
    console.log(`Referință relativă setată la: ${relativeTo}`);
  }
  // // Functii helper
  getPercentageDisplay(county: CountyData | null): string {
    if (!county || county.percentage === undefined) return '0.00';
    return (county.percentage * 100).toFixed(2);
  }
  
   // Functionalitate imbunatatita pentru descarcarea CSV-ului
  downloadCSV(): void {
    console.log('Descărcare CSV inițiată');
    
    if (!this.countyData) {
      console.error('Nu există date disponibile pentru descărcare');
      return;
    }
    
    // Creaza continutul CSV cu date detaliate
    const headers = [
      'Judet', 
      'Cod', 
      'Inscrisi pe liste permanente', 
      'Sectii de votare', 
      'Votanti pe liste permanente', 
      'Votanti pe liste suplimentare', 
      'Votanti cu urna mobila', 
      'Total votanti', 
      'Prezenta(%)'
    ];
    const csvRows = [headers.join(',')];
    
    Object.values(this.countyData).forEach((county: CountyData) => {
      const row = [
        county.name,
        county.code,
        county.registeredVoters,
        county.pollingStationCount,
        county.permanentListVoters,
        county.supplementaryListVoters,
        county.mobileUrnsVoters,
        county.totalVoters,
        typeof county.turnoutPercentage === 'string' ? county.turnoutPercentage : county.turnoutPercentage + '%'
      ];
      csvRows.push(row.join(','));
    });
    
    const csvContent = csvRows.join('\n');
    
     // Creeaza un blob si descarca fisierul
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    // Nume de fisier cu timestamp
    const date = new Date();
    const timestamp = date.toISOString().slice(0, 10);
    
    link.setAttribute('href', url);
    link.setAttribute('download', 'date_judete_' + timestamp + '.csv');
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}