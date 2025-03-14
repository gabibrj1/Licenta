import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, Renderer2, NgZone } from '@angular/core';
import { MapService, MapInfo } from '../services/map.service';
import * as d3 from 'd3';

interface CountyData {
  name: string;
  code: string;
  voters: number;
  percentage: number;
  // New fields for enhanced statistics
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
  
  // Map configuration
  mapLevel: string = 'judete';
  highlightField: string = 'prezenta';
  relativeTo: string = 'maxim';
  
  // Data
  geoJsonData: any = null;
  countyData: { [key: string]: CountyData } = {};
  
  // UI state
  isLoading: boolean = true;
  hoveredCounty: CountyData | null = null;
  hoverPosition = { x: 0, y: 0 };
  
  // Stats
  totalVoters: string = '53.675';
  totalPercentage: string = '0.30';
  maxValue: string = '100';
  minValue: string = '-1';
  
  // Map rendering
  private svg: any;
  private projection: any;
  private path: any;
  private zoom: any;
  private g: any;
  
  constructor(
    private mapService: MapService,
    private renderer: Renderer2,
    private ngZone: NgZone
  ) {}

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
    
    // First load the voting statistics from CSV
    this.mapService.getVotingStatistics().subscribe({
      next: (votingStats) => {
        console.log('MapComponent: Date CSV primite cu succes');
        
        // Load GeoJSON data
        this.loadGeoJsonData().then(geoData => {
          console.log('MapComponent: Date GeoJSON primite cu succes');
          this.geoJsonData = geoData;
          
          // Load county statistics
          this.mapService.getMapInfo().subscribe({
            next: (countyStats: MapInfo) => {
              console.log('MapComponent: Date statistice primite cu succes');
              
              // Process and merge data
              if (countyStats && countyStats.regions) {
                countyStats.regions.forEach((region: CountyData) => {
                  const csvData = votingStats[region.code] || {};
                  
                  // Combină datele și asigură-te că toate proprietățile există
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
              
              // Initialize map after data is loaded
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
        
        // Continue loading other data even if CSV fails
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
  
  initializeMap(): void {
    if (!this.geoJsonData || !this.mapContainer) return;
    
    this.ngZone.runOutsideAngular(() => {
      // Clear any existing SVG
      const container = this.mapContainer.nativeElement;
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
      
      // Get container dimensions
      const width = container.clientWidth;
      const height = container.clientHeight || 500;
      
      // Create SVG
      this.svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .attr('class', 'romania-map');
      
      // Create projection
      this.projection = d3.geoMercator()
        .fitSize([width, height], this.geoJsonData);
      
      // Create path generator
      this.path = d3.geoPath().projection(this.projection);
      
      // Setup zoom behavior
      this.zoom = d3.zoom()
        .scaleExtent([1, 8])
        .on('zoom', (event) => {
          this.g.attr('transform', event.transform);
        });
      
      // Apply zoom behavior to SVG
      this.svg.call(this.zoom);
      
      // Create a group for all map elements
      this.g = this.svg.append('g');
      
      // Draw counties
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
      
      // Add county labels
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
  
  getCountyCode(feature: GeoFeature): string {
    // Map from county name to county code
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
    
    // Get the county name from feature properties
    const name = feature.properties.name;
    
    // Return the county code or the name if not found
    return countyCodeMap[name] || name;
  }
  
  handleCountyMouseOver(event: any, feature: GeoFeature): void {
    const countyCode = this.getCountyCode(feature);
    const countyData = this.countyData[countyCode];
    
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
    
    // Setează poziția tooltip-ului
    this.hoverPosition = {
      x: event.clientX,
      y: event.clientY - 70
    };
    
    // Schimbă culoarea județelor
    d3.select(event.target as SVGPathElement)
      .attr('fill', '#0066cc');
  }
  
  handleCountyMouseMove(event: any): void {
    // Update tooltip position
    this.hoverPosition = {
      x: event.clientX,
      y: event.clientY - 70
    };
  }
  
  handleCountyMouseOut(event: any, feature: GeoFeature): void {
    const countyCode = this.getCountyCode(feature);
    
    // Reset county color
    d3.select(event.target as SVGPathElement)
      .attr('fill', this.getCountyColor(countyCode));
    
    // Clear hovered county
    this.hoveredCounty = null;
  }
  
  handleCountyClick(feature: GeoFeature): void {
    const countyCode = this.getCountyCode(feature);
    console.log(`Județ selectat: ${feature.properties.name} (${countyCode})`);
    
    // Add implementation for county click action
  }
  
  // Method to load GeoJSON data
  private loadGeoJsonData(): Promise<any> {
    return new Promise((resolve, reject) => {
      // Using fetch API to load the GeoJSON file
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
  
  getCountyColor(countyCode: string): string {
    const county = this.countyData[countyCode];
    if (!county) return '#d0d0ff';
    
    // Calculate color based on percentage
    const percentage = county.percentage;
    if (percentage > 0.6) return '#4050e0';
    if (percentage > 0.4) return '#6070e0';
    if (percentage > 0.2) return '#8090e0';
    if (percentage > 0.1) return '#a0b0e0';
    return '#c0d0ff';
  }
  
  // Filter controls
  setMapLevel(level: string): void {
    this.mapLevel = level;
    // Implement logic to switch between county and UAT levels
  }
  
  setHighlightField(field: string): void {
    this.highlightField = field;
    // Implement logic to change highlighted field
  }
  
  setRelativeTo(relativeTo: string): void {
    this.relativeTo = relativeTo;
    // Implement logic to change relative measurement
  }
  
  // Helper methods
  getPercentageDisplay(county: CountyData | null): string {
    if (!county || county.percentage === undefined) return '0.00';
    return (county.percentage * 100).toFixed(2);
  }
  
  downloadCSV(): void {
    console.log('Descărcare CSV inițiată');
    
    if (!this.countyData) {
      console.error('Nu există date disponibile pentru descărcare');
      return;
    }
    
    // Create CSV content
    const headers = ['Județ', 'Cod', 'Număr Votanți', 'Procentaj'];
    const csvRows = [headers.join(',')];
    
    Object.values(this.countyData).forEach((county: CountyData) => {
      const row = [
        county.name,
        county.code,
        county.voters,
        (county.percentage * 100).toFixed(2) + '%'
      ];
      csvRows.push(row.join(','));
    });
    
    const csvContent = csvRows.join('\n');
    
    // Create a blob and download the file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', 'date_judete_' + new Date().toISOString().slice(0, 10) + '.csv');
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}