import { Component, OnInit } from '@angular/core';
import { MapService } from '../services/map.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})
export class MapComponent implements OnInit {
  mapInfo: any = null;
  isLoading: boolean = true;
  selectedRegion: string = 'romania'; // Default region
  
  constructor(
    private mapService: MapService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    console.log('MapComponent: ngOnInit a fost apelat');
    this.loadMapInfo();
  }

  loadMapInfo(): void {
    console.log('MapComponent: Începe încărcarea informațiilor hartă');
    this.isLoading = true;
    
    this.mapService.getMapInfo().subscribe({
      next: (data) => {
        console.log('MapComponent: Date primite cu succes:', data);
        this.mapInfo = data;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('MapComponent: Eroare la încărcarea datelor:', error);
        this.snackBar.open('Nu s-au putut încărca informațiile hartă', 'Închide', {
          duration: 3000,
          panelClass: ['error-snackbar']
        });
        this.isLoading = false;
      },
      complete: () => {
        console.log('MapComponent: Încărcare completă');
        this.isLoading = false;
      }
    });
  }
  
  switchRegion(region: string): void {
    this.selectedRegion = region;
    // You could reload data specific to this region if needed
  }
}