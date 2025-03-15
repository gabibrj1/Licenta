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
      .scaleExtent([1, 8]) // limitele de zoom
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
      
      // Adauga etichete pentru judete
      this.g.selectAll('.county-label')
        .data(this.geoJsonData.features)
        .enter()
        .append('text')
        .attr('class', 'county-label')
        .attr('x', (d: GeoFeature) => this.path.centroid(d)[0])
        .attr('y', (d: GeoFeature) => this.path.centroid(d)[1])
        .attr('text-anchor', 'middle')
        .attr('alignment-baseline', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#fff')
        .text((d: GeoFeature) => this.getCountyCode(d))
        .attr('pointer-events', 'none');
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
      
      // Actualizeaza pozitiile etichetelor
      this.g.selectAll('.county-label')
        .attr('x', (d: GeoFeature) => this.path.centroid(d)[0])
        .attr('y', (d: GeoFeature) => this.path.centroid(d)[1]);
      
      // Reaplica transformarea curenta
      this.g.attr('transform', this.currentTransform);
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
  handleCountyClick(feature: GeoFeature): void {
    const countyCode = this.getCountyCode(feature);
    console.log(`Județ selectat: ${feature.properties.name} (${countyCode})`);
    
    // Zoom pe judetul selectat
    if (this.svg && this.path) {
      const bounds = this.path.bounds(feature);
      const dx = bounds[1][0] - bounds[0][0];
      const dy = bounds[1][1] - bounds[0][1];
      const x = (bounds[0][0] + bounds[1][0]) / 2;
      const y = (bounds[0][1] + bounds[1][1]) / 2;
      
      const container = this.mapContainer.nativeElement;
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      // Calculeaza scara si translatia pentru zoom
      const scale = Math.min(5, 0.9 / Math.max(dx / width, dy / height));
      const translate = [width / 2 - scale * x, height / 2 - scale * y];
      
      // Aplica transformarea pentru zoom
      this.svg.transition()
        .duration(750)
        .call(this.zoom.transform, d3.zoomIdentity
          .translate(translate[0], translate[1])
          .scale(scale));
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
  getCountyColor(countyCode: string): string {
    const county = this.countyData[countyCode];
    if (!county) return '#d0d0ff'; // Culoare implicita pentru judete fara date
    
    // Obtine procentajul de prezenta pentru judet (turnoutPercentage)
    let turnoutValue = 0;
    if (typeof county.turnoutPercentage === 'string') {
      turnoutValue = parseFloat(county.turnoutPercentage);
    } else {
      turnoutValue = county.turnoutPercentage as number;
    }
    
    //  Daca procentajul judetului este foarte aproape de valoarea slider-ului (toleranță de 0.1%)
    if (Math.abs(turnoutValue - this.filterPercentage) < 0.1) {
      // Evidentiaza judetele care se potrivesc exact cu filtrul
      return '#1f1f1f'; // Culoare contrastanta pentru judetele la pragul de filtrare
    }
    
    // Pentru toate celelalte judete, foloseste schema de culori normala
    const percentage = county.percentage;
    if (percentage > 0.6) return '#4050e0';
    if (percentage > 0.4) return '#6070e0';
    if (percentage > 0.2) return '#8090e0';
    if (percentage > 0.1) return '#a0b0e0';
    return '#c0d0ff';
  }
// Metoda pentru actualizarea filtrului
onFilterChange(): void {
  // Actualizeaza culorile judetelor pe baza noului filtru
  if (this.g) {
    this.g.selectAll('.county-path')
      .attr('fill', (d: GeoFeature) => this.getCountyColor(this.getCountyCode(d)));
  }
  
  // Actualizeaza statisticile globale
  this.updateGlobalStats();
}

// Metoda pentru actualizarea statisticilor globale
updateGlobalStats(): void {
  // Calculeaza numarul de judete la pragul ales
  let countiesAtThreshold = 0;
  let totalCounties = 0;
  
  Object.values(this.countyData).forEach(county => {
    totalCounties++;
    let turnoutValue = 0;
    if (typeof county.turnoutPercentage === 'string') {
      turnoutValue = parseFloat(county.turnoutPercentage);
    } else {
      turnoutValue = county.turnoutPercentage as number;
    }
    
    if (Math.abs(turnoutValue - this.filterPercentage) < 0.1) {
      countiesAtThreshold++;
    }
  });

      // Actualizeaza statisticile afisate
      this.totalPercentage = this.filterPercentage.toFixed(2);
      this.totalVoters = countiesAtThreshold.toString();
  
  console.log(`Județe cu prezență de ${this.filterPercentage}%: ${countiesAtThreshold}`);
}
   // Metode de control pentru filtre
  setMapLevel(level: string): void {
    this.mapLevel = level;
   // Implementeaza logica pentru comutarea intre nivele judete si UAT
   console.log(`Nivel hartă setat la: ${level}`);
  }
  
  setHighlightField(field: string): void {
    this.highlightField = field;
    // Recoloreza judetele in functie de noul camp
    if (this.g) {
      this.g.selectAll('.county-path')
        .attr('fill', (d: GeoFeature) => this.getCountyColor(this.getCountyCode(d)));
    }
    console.log(`Câmp evidențiere setat la: ${field}`);
  }
  
  setRelativeTo(relativeTo: string): void {
    this.relativeTo = relativeTo;
    // Actualizeaza visualizarea
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