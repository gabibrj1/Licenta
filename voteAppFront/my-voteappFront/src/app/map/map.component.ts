import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, Renderer2, NgZone, HostListener } from '@angular/core';
import { MapService, MapInfo } from '../services/map.service';
import * as d3 from 'd3';
import { Router } from '@angular/router';

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

  // Valorile pentru filtrare
  filterPercentage: number = 0;
  
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

  // Variabile pentru harta cu UAT-uri
  selectedCounty: string | null = null;
  uatGeoJsonData: any = null;
  isUATView: boolean = false;
  countyOptions: {code: string, name: string}[] = [];
  
  constructor(
    private mapService: MapService,
    private renderer: Renderer2,
    private ngZone: NgZone,
    private router: Router,
  ) {}
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
    this.loadMapData();
  }

  ngAfterViewInit(): void {
    // Initialize map when the view is ready
    if (!this.isLoading && this.geoJsonData) {
      this.initializeMap();
    }
  }

  loadMapData(): void {
    console.log('MapComponent: Începe încărcarea datelor hartă');
    this.isLoading = true;
    
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
      });
      
      // Aplica zoom-ul la SVG
      this.svg.call(this.zoom);
      
      // Creaza un grup pentru toate elementele hartii
      this.g = this.svg.append('g');
      
      // Deseneaza judetele
      this.g.selectAll('.county-path')
        .data(this.geoJsonData.features)
        .enter()
        .append('path')
        .attr('class', 'county-path')
        .attr('id', (d: GeoFeature) => this.getCountyCode(d))
        .attr('d', this.path)
        .attr('fill', (d: GeoFeature) => this.getCountyColor(this.getCountyCode(d)))
        .attr('stroke', '#fff')
        .attr('stroke-width', 0.5)
        .on('mouseover', (event: MouseEvent, d: GeoFeature) => {
          this.ngZone.run(() => this.handleCountyMouseOver(event, d));
        })
        .on('mousemove', (event: MouseEvent) => {
          this.ngZone.run(() => this.handleCountyMouseMove(event));
        })
        .on('mouseout', (event: MouseEvent, d: GeoFeature) => {
          this.ngZone.run(() => this.handleCountyMouseOut(event, d));
        })
        .on('click', (event: MouseEvent, d: GeoFeature) => {
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
          // Dacă este selectat "sectii", codul județului va fi puțin mai sus
          return this.highlightField === 'sectii' ? -5 : 0;
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
        
      // ADAUGĂ AICI - La finalul funcției, după ce toate elementele SVG au fost create
      // Trebuie să fie în interiorul ngZone.run() pentru că funcția va actualiza UI
      this.ngZone.run(() => {
        // Inițializează setările hărții pentru a aplica efectele vizuale corecte
        this.initializeMapSettings();
      });
    });
  }
  // Metoda pentru redimensionarea hartii la redimensionarea ferestrei
  resizeMap(): void {
    if (!this.svg || !this.mapContainer) return;
    
    this.ngZone.runOutsideAngular(() => {
      const container = this.mapContainer.nativeElement;
      const width = container.clientWidth;
      const height = container.clientHeight || 500;
      
      // Actualizeaza dimensiunile SVG-ului
      this.svg
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
      
      // Actualizeaza proiectia
      this.projection.fitExtent([[20, 20], [width - 20, height - 20]], this.geoJsonData);
      
      // Actualizeaza path-urile pentru judete
      this.g.selectAll('.county-path')
        .attr('d', this.path);
      
      // Actualizeaza pozitiile grupurilor etichetelor
      this.g.selectAll('.county-label-group')
        .attr('transform', (d: GeoFeature) => {
          const centroid = this.path.centroid(d);
          return `translate(${centroid[0]}, ${centroid[1]})`;
        });
      
      // Verificăm starea highlightField pentru a menține vizibilitatea numărului de secții
      this.g.selectAll('.county-label')
        .attr('y', this.highlightField === 'sectii' ? -5 : 0);
        
      this.g.selectAll('.polling-station-count')
        .attr('opacity', this.highlightField === 'sectii' ? 1 : 0);
      
      // Reaplica transformarea curenta
      this.zoom = d3.zoom()
        .scaleExtent([0.3, 9])
        .translateExtent([[0, 0], [width, height]])
        .on('zoom', (event) => {
          // Actualizeaza transformarea curenta
          this.currentTransform = event.transform;
          
          // Aplică transformarea corect
          this.g.attr('transform', `translate(${event.transform.x},${event.transform.y}) scale(${event.transform.k})`);
          
          // Ajusteaza grosimea conturului in functie de zoom
          const strokeWidth = 0.5 / event.transform.k;
          this.g.selectAll('.county-path, .uat-path')
            .attr('stroke-width', strokeWidth);
            
          // Ajustează dimensiunea textului
          const fontSize = 10 / event.transform.k;
          this.g.selectAll('.county-label, .polling-station-count')
            .attr('font-size', `${fontSize}px`);
        });
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
    const countyCode = this.getCountyCode(feature);
    const countyData = this.countyData[countyCode];
    
    // Verifica daca avem date pentru judet
    if (countyData) {
      // Asigura-te ca toate proprietatile necesare exista in obiect
      this.hoveredCounty = {
        name: countyData.name || feature.properties.name,
        code: countyCode,
        voters: countyData.voters || 0,
        percentage: countyData.percentage || 0,
        
        // Adauga explicit proprietatile din statistici
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
      // Daca nu avem date, foloseste un obiect gol cu valori implicite
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
    // Calculeaza pozitia corecta a tooltip-ului in functie de zoom
    // Ajustare pentru a preveni aparitia tooltip-ului in afara ecranului
    const mapRect = this.mapContainer.nativeElement.getBoundingClientRect();
    const x = event.clientX - mapRect.left;
    const y = event.clientY - mapRect.top;
    
    // Setează poziția tooltip-ului
    const tooltipWidth = 280; // Latime aproximativa tooltip
    const tooltipHeight = 250; // Inaltime aproximativa tooltip
    
    let posX = x;
    let posY = y;
    
    // Ajustare orizontala - previne iesirea din dreapta
    if (x + tooltipWidth > mapRect.width) {
      posX = x - tooltipWidth;
    }
    
    // Ajustare verticala - previne iesirea din jos
    if (y + tooltipHeight > mapRect.height) {
      posY = y - tooltipHeight;
    }
    
    // Asigura-te ca tooltip-ul nu iese din stanga sau sus
    posX = Math.max(10, posX);
    posY = Math.max(10, posY);
    
    this.hoverPosition = {
      x: posX,
      y: posY
    };
    
    // Schimbă culoarea județelor
    d3.select(event.target as SVGPathElement)
      .attr('fill', '#0066cc');
  }
  
  // Gestioneaza miscarea mouse ului peste un judet
  handleCountyMouseMove(event: any): void {
    if (!this.hoveredCounty) return; // Iesi daca nu avem un judet hover
    
    // Calculeaza pozitia tooltip-ului in interiorul containerului hartii
    const mapRect = this.mapContainer.nativeElement.getBoundingClientRect();
    const x = event.clientX - mapRect.left;
    const y = event.clientY - mapRect.top;
    
    // Verifica marginile pentru a ne asigura ca tooltip-ul ramane in container
    const tooltipWidth = 280;
    const tooltipHeight = 250;
    
    let posX = x;
    let posY = y;
    
    // Ajustare orizontala - previne iesirea din dreapta
    if (x + tooltipWidth > mapRect.width) {
      posX = x - tooltipWidth;
    }
    
    // Ajustare verticala - previne iesirea din jos
    if (y + tooltipHeight > mapRect.height) {
      posY = y - tooltipHeight;
    }
    
    // Asigura-te ca tooltip-ul nu iese din stanga sau sus
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
    
    // Reseteza culoarea judetului
    d3.select(event.target as SVGPathElement)
      .attr('fill', this.getCountyColor(countyCode));
    
    // Sterge judetul hover
    this.hoveredCounty = null;
  }
  
  // Gestioneaza click-ul pe un judet
// Gestionează click-ul pe un județ
handleCountyClick(feature: GeoFeature): void {
  const countyCode = this.getCountyCode(feature);
  console.log(`Județ selectat: ${feature.properties.name} (${countyCode})`);
  
  // Opțional: întreabă utilizatorul dacă dorește să vadă UAT-urile pentru acest județ
  if (confirm(`Doriți să vizualizați UAT-urile pentru județul ${feature.properties.name}?`)) {
    this.mapLevel = 'uaturi';
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
  if (!county) return '#d0d0ff'; // Culoare implicita pentru judete fara date
  
  // Verifică dacă suntem în modul "secții de votare"
  if (this.highlightField === 'sectii') {
    // În modul secții, folosim pollingStationCount pentru filtrare
    const stationCount = county.pollingStationCount || 0;
    
    // Dacă numărul de secții este foarte aproape de valoarea sliderului (toleranță de 1)
    if (stationCount >= this.filterPercentage)  {
      // Evidențiem acest județ cu o culoare contrastantă
      return '#1f1f1f'; // Culoare contrastantă pentru județele la pragul de filtrare
    }
    
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
  // Actualizează culorile județelor pe baza noului filtru
  if (this.g) {
    this.g.selectAll('.county-path')
      .attr('fill', (d: GeoFeature) => this.getCountyColor(this.getCountyCode(d)));
  }
  
  // Actualizează statisticile globale
  this.updateGlobalStats();
  
  // Actualizează textul de filtrare
  this.updateFilterText();
}

// Metoda pentru actualizarea statisticilor globale
updateGlobalStats(): void {
  if (this.highlightField === 'sectii') {
    // Pentru modul "secții de votare"
    let countiesAboveThreshold = 0;
    let totalCounties = 0;
    let totalStations = 0;
    
    Object.values(this.countyData).forEach(county => {
      totalCounties++;
      const stationCount = county.pollingStationCount || 0;
      totalStations += stationCount;
      
      if (stationCount >= this.filterPercentage) {
        countiesAboveThreshold++;
      }
    });
    
    // Actualizează statisticile afișate
    this.totalVoters = countiesAboveThreshold.toString();
    this.totalPercentage = (countiesAboveThreshold / totalCounties * 100).toFixed(2);
    
    console.log(`Județe cu cel puțin ${this.filterPercentage} secții: ${countiesAboveThreshold}`);
  } else {
    // Pentru alte moduri (prezență, votanți)
    // Calculeaza numărul de județe la pragul ales
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
        // Pentru alte câmpuri, folosim logica originală
        if (Math.abs(county.percentage * 100 - this.filterPercentage) < 0.1) {
          countiesAtThreshold++;
        }
      }
    });

    // Actualizează statisticile afișate
    this.totalPercentage = this.filterPercentage.toFixed(2);
    this.totalVoters = countiesAtThreshold.toString();
    
    console.log(`Județe cu prezență de ${this.filterPercentage}%: ${countiesAtThreshold}`);
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
  loadCountyUATMap(countyCode: string): void {
    if (!countyCode) return;
    
    console.log('Încărcare hartă UAT pentru județul:', countyCode);
    
    // Setează loading și starea vizualizării
    this.isLoading = true;
    this.selectedCounty = countyCode;
    this.isUATView = true;
    
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
        
        // Actualizează selectorul de județe (dacă există)
        setTimeout(() => {
          const countySelector = document.getElementById('county-select') as HTMLSelectElement;
          if (countySelector) {
            countySelector.value = countyCode;
          }
          
          // Verifică dacă mapContainer este disponibil după actualizarea DOM
          if (this.mapContainer) {
            this.initializeUATMap();
          } else {
            console.error('Container hartă (mapContainer) nu este disponibil după actualizarea DOM');
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
          .attr('fill', '#80a0e0')
          .attr('stroke', '#fff')
          .attr('stroke-width', 0.5);
        
        console.log('Număr de path-uri create:', paths.size());
        
        // Adaugă evenimente de hover
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
        
        // Am eliminat butonul Înapoi din SVG, îl vom folosi pe cel din HTML
        
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
    
    // Actualizează valorile sliderului în funcție de câmpul selectat
    if (field === 'sectii') {
      // Pentru secții de votare, găsește valorile minime și maxime
      let minPollingStations = Number.MAX_VALUE;
      let maxPollingStations = 0;
      
      Object.values(this.countyData).forEach(county => {
        // Asigură-te că folosim numere pentru comparație
        const stationCount = Number(county.pollingStationCount || 0);
        
        if (stationCount < minPollingStations) minPollingStations = stationCount;
        if (stationCount > maxPollingStations) maxPollingStations = stationCount;
        
        // Log pentru București pentru debugging
        if (county.code === 'B') {
          console.log(`București - pollingStationCount: ${county.pollingStationCount} (tipul: ${typeof county.pollingStationCount})`);
          console.log(`București - stationCount convertit: ${stationCount}`);
        }
      });
      
      console.log(`Valoare minimă secții: ${minPollingStations}, Valoare maximă secții: ${maxPollingStations}`);
      
      // Asigură-te că maxPollingStations este cel puțin minPollingStations+1
      if (maxPollingStations <= minPollingStations) {
        maxPollingStations = minPollingStations + 1;
      }
      
      // Adaugă 1 la maxPollingStations pentru a permite ajustarea slider-ului la valoarea maximă exactă
      maxPollingStations = maxPollingStations + 1;
      
      // Setează valorile pentru slider
      this.minValue = minPollingStations.toString();
      this.maxValue = maxPollingStations.toString();
      
      // IMPORTANT: Setează valoarea sliderului la minim pentru a nu colora județele la început
      this.filterPercentage = minPollingStations;
      
      // Actualizează slider-ul cu valorile corecte
      setTimeout(() => {
        const slider = document.querySelector('.percentage-slider') as HTMLInputElement;
        if (slider) {
          slider.min = minPollingStations.toString();
          slider.max = maxPollingStations.toString();
          slider.value = minPollingStations.toString();
          slider.step = '1'; // Pentru secții de votare, pasul ar trebui să fie număr întreg
          
          console.log(`Slider configurat cu min: ${slider.min}, max: ${slider.max}, valoare: ${slider.value}`);
        }
        
        // Actualizează și etichetele min/max
        const minLabel = document.querySelector('.min-label span');
        const maxLabel = document.querySelector('.max-label span');
        if (minLabel) minLabel.textContent = minPollingStations.toString();
        if (maxLabel) maxLabel.textContent = maxPollingStations.toString();
      }, 0);
    } else {
      // Pentru alte câmpuri, revenirea la valorile procentuale
      this.minValue = '0';
      this.maxValue = '100';
      this.filterPercentage = 0;
      
      // Păstrează relativeTo la valoarea curentă dacă suntem în câmpul prezență
      // Nu resetăm valoarea pentru a respecta setarea utilizatorului
      if (field === 'prezenta') {
        // Nu mai setăm default la 'maxim', păstrăm valoarea curentă
        // Aplicăm efectul vizual corect în funcție de relativeTo actual
        this.applyRelativeToEffect();
      }
      
      // Actualizează element-ul DOM pentru slider
      setTimeout(() => {
        const slider = document.querySelector('.percentage-slider') as HTMLInputElement;
        if (slider) {
          slider.min = '0';
          slider.max = '100';
          slider.value = '0';
          slider.step = '0.1';
        }
        
        // Actualizează și etichetele min/max
        const minLabel = document.querySelector('.min-label span');
        const maxLabel = document.querySelector('.max-label span');
        if (minLabel) minLabel.textContent = '0';
        if (maxLabel) maxLabel.textContent = '100';
        
        // Actualizează maxima sliderului în funcție de relativeTo dacă suntem în modul prezență
        if (field === 'prezenta') {
          this.updateSliderMaxForTurnout();
        }
      }, 0);
    }
    
    // Recolorează județele
    if (this.g) {
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
    }
    
    // Actualizează textul pentru filtru
    this.updateFilterText();
  }

  updateFilterText(): void {
    setTimeout(() => {
      const filterValueElement = document.querySelector('.filter-value span');
      if (filterValueElement) {
        if (this.highlightField === 'sectii') {
          filterValueElement.textContent = `Filtrare: ${Math.round(this.filterPercentage)} secții`;
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
        .attr('fill', 'rgba(0, 0, 0, 0.15)')  // O tentă ușor umbrita
        .attr('opacity', 0);  // Inițial invizibil
    }
    
    // Aplicăm efectul de overlay
    if (this.relativeTo === 'total') {
      // Pentru modul 100%, afișăm overlay-ul cu o tranziție
      overlay.transition()
        .duration(300)
        .attr('opacity', 1);
    } else {
      // Pentru modul maxim, ascundem overlay-ul cu o tranziție
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