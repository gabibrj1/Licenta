import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PresenceService } from '../services/presence.service';
import { interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-presence',
  templateUrl: './presence.component.html',
  styleUrls: ['./presence.component.scss']
})
export class PresenceComponent implements OnInit, OnDestroy {
  presenceData: any = null;
  liveData: any = null;
  isLoading = true;
  error = '';
  
  // Parametri de control
  currentLocation = 'romania';
  currentRound = 'tur1_2024';
  isLiveMode = false;
  
  // Pentru paginare
  currentPage = 1;
  pageSize = 10;
  
  // Pentru countdown
  timeRemaining = 0;
  countdownDisplay = '';
  
  // Opțiuni pentru grafice
  generalChartOptions: any = {};
  urbanRuralChartOptions: any = {};
  countyChartOptions: any = {};
  evolutionChartOptions: any = {};
  
  // Subscriptions pentru auto-refresh
  private refreshSubscription?: Subscription;
  private countdownSubscription?: Subscription;
  
  constructor(
    private presenceService: PresenceService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    // Ascultă schimbările de parametri din rută
    this.route.queryParams.subscribe(params => {
      this.currentLocation = params['location'] || 'romania';
      this.currentRound = params['round'] || 'tur1_2024';
      this.currentPage = parseInt(params['page']) || 1;
      
      this.isLiveMode = this.currentRound === 'tur_activ';
      
      this.loadPresenceData();
      
      // Configurează auto-refresh pentru modul live
      if (this.isLiveMode) {
        this.startLiveUpdates();
      } else {
        this.stopLiveUpdates();
      }
    });
  }

  ngOnDestroy(): void {
    this.stopLiveUpdates();
    this.stopCountdown();
  }

  loadPresenceData(): void {
    this.isLoading = true;
    this.error = '';
    
    this.presenceService.getVotingPresence(this.currentLocation, this.currentRound, this.currentPage, this.pageSize)
      .subscribe({
        next: (data) => {
          this.presenceData = data;
          this.setupCharts();
          this.setupCountdown();
          this.isLoading = false;
        },
        error: (error) => {
          this.error = 'Eroare la încărcarea datelor de prezență: ' + (error.error?.message || error.message);
          this.isLoading = false;
        }
      });
  }

  startLiveUpdates(): void {
    // Actualizează la fiecare 30 secunde în modul live
    this.refreshSubscription = interval(30000)
      .pipe(
        switchMap(() => this.presenceService.getLivePresence())
      )
      .subscribe({
        next: (liveData) => {
          this.liveData = liveData;
          this.timeRemaining = liveData.time_remaining || 0;
          this.loadPresenceData(); // Reîncarcă și datele generale
        },
        error: (error) => {
          console.error('Eroare la actualizarea live:', error);
        }
      });
  }

  stopLiveUpdates(): void {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  setupCountdown(): void {
    this.stopCountdown();
    
    if (this.isLiveMode && this.timeRemaining > 0) {
      this.countdownSubscription = interval(1000).subscribe(() => {
        if (this.timeRemaining > 0) {
          this.timeRemaining--;
          this.updateCountdownDisplay();
        } else {
          this.stopCountdown();
        }
      });
    }
  }

  stopCountdown(): void {
    if (this.countdownSubscription) {
      this.countdownSubscription.unsubscribe();
    }
  }

  updateCountdownDisplay(): void {
    const hours = Math.floor(this.timeRemaining / 3600);
    const minutes = Math.floor((this.timeRemaining % 3600) / 60);
    const seconds = this.timeRemaining % 60;
    
    this.countdownDisplay = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  setupCharts(): void {
    if (!this.presenceData) return;

    this.setupGeneralChart();
    this.setupUrbanRuralChart();
    this.setupCountyChart();
    this.setupEvolutionChart();
  }

  setupGeneralChart(): void {
    const stats = this.presenceData.general_stats;
    
    this.generalChartOptions = {
      title: {
        text: 'Prezența Generală la Vot',
        left: 'center',
        textStyle: {
          color: '#ffffff',
          fontSize: 16
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: {
          color: '#ffffff'
        }
      },
      series: [
        {
          name: 'Prezența la vot',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          data: [
            {
              value: stats.total_voters,
              name: `Au votat (${this.formatNumber(stats.total_voters)})`,
              itemStyle: { color: '#4CAF50' }
            },
            {
              value: stats.registered_permanent - stats.total_voters,
              name: `Nu au votat (${this.formatNumber(stats.registered_permanent - stats.total_voters)})`,
              itemStyle: { color: '#757575' }
            }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          label: {
            formatter: '{d}%',
            color: '#ffffff'
          }
        }
      ]
    };
  }

  setupUrbanRuralChart(): void {
    const urbanRural = this.presenceData.urban_rural;
    
    this.urbanRuralChartOptions = {
      title: {
        text: '',
        left: 'center',
        textStyle: {
          color: '#ffffff',
          fontSize: 16
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['Votanți', 'Rata de participare'],
        textStyle: {
          color: '#ffffff'
        }
      },
      xAxis: [
        {
          type: 'category',
          data: ['Urban', 'Rural'],
          axisPointer: {
            type: 'shadow'
          },
          axisLabel: {
            color: '#ffffff'
          }
        }
      ],
      yAxis: [
        {
          type: 'value',
          name: 'Votanți',
          min: 0,
          axisLabel: {
            color: '#ffffff',
            formatter: (value: number) => this.formatNumber(value)
          }
        },
        {
          type: 'value',
          name: 'Rata de participare (%)',
          min: 0,
          max: 100,
          axisLabel: {
            color: '#ffffff',
            formatter: '{value}%'
          }
        }
      ],
      series: [
        {
          name: 'Votanți',
          type: 'bar',
          data: [urbanRural.urban.voters, urbanRural.rural.voters],
          itemStyle: {
            color: '#2196F3'
          }
        },
        {
          name: 'Rata de participare',
          type: 'line',
          yAxisIndex: 1,
          data: [urbanRural.urban.participation_rate, urbanRural.rural.participation_rate],
          itemStyle: {
            color: '#FF9800'
          }
        }
      ]
    };
  }

setupCountyChart(): void {
  const counties = this.presenceData.counties.slice(0, 10); // Top 10 județe/țări
  
  // Create shortened names for display
  const displayNames = counties.map((c: any) => {
    const name = c.county;
    if (name.length > 15) {
      return name.substring(0, 12) + '...';
    }
    return name;
  });

  this.countyChartOptions = {
    title: {
      text: `Top 10 ${this.currentLocation === 'romania' ? 'Județe' : 'Țări'} - Prezența la Vot`,
      left: 'center',
      textStyle: {
        color: '#ffffff',
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const data = params[0];
        const county = counties[data.dataIndex];
        return `
          <div class="tooltip-title">${county.county}</div>
          <div class="tooltip-content">
            Votanți: ${this.formatNumber(county.total_voters)}<br/>
            Rata de participare: ${county.participation_rate.toFixed(1)}%<br/>
            Înscriși: ${this.formatNumber(county.registered_permanent)}
          </div>
        `;
      }
    },
    xAxis: {
      type: 'category',
      data: displayNames, // Use shortened names for display
      axisLabel: {
        color: '#ffffff',
        rotate: 30,
        interval: 0,
        formatter: (value: string, index: number) => {
          // Show full name on hover
          return value;
        }
      },
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#ffffff',
        formatter: (value: number) => this.formatNumber(value)
      }
    },
    series: [
      {
        type: 'bar',
        data: counties.map((c: any) => c.total_voters),
        itemStyle: {
          color: '#4CAF50'
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => {
            return this.formatNumber(params.value);
          },
          color: '#ffffff'
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ],
    dataZoom: [
      {
        type: 'slider',
        show: true,
        xAxisIndex: [0],
        start: 0,
        end: 100,
        height: 20,
        bottom: 10,
        handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
        handleSize: '80%',
        handleStyle: {
          color: '#fff',
          shadowBlur: 3,
          shadowColor: 'rgba(0, 0, 0, 0.6)',
          shadowOffsetX: 2,
          shadowOffsetY: 2
        }
      }
    ]
  };
}

  setupEvolutionChart(): void {
    if (!this.liveData?.hourly_evolution) {
      this.evolutionChartOptions = null;
      return;
    }
    
    const evolution = this.liveData.hourly_evolution;
    
    this.evolutionChartOptions = {
      title: {
        text: 'Evoluția Prezentei pe Ore',
        left: 'center',
        textStyle: {
          color: '#ffffff',
          fontSize: 16
        }
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['Voturi pe oră', 'Total cumulativ'],
        textStyle: {
          color: '#ffffff'
        }
      },
      xAxis: {
        type: 'category',
        data: evolution.map((item: any) => item.hour),
        axisLabel: {
          color: '#ffffff'
        }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Voturi pe oră',
          position: 'left',
          axisLabel: {
            color: '#ffffff'
          }
        },
        {
          type: 'value',
          name: 'Total cumulativ',
          position: 'right',
          axisLabel: {
            color: '#ffffff'
          }
        }
      ],
      series: [
        {
          name: 'Voturi pe oră',
          type: 'bar',
          data: evolution.map((item: any) => item.votes),
          itemStyle: {
            color: '#3498db'
          }
        },
        {
          name: 'Total cumulativ',
          type: 'line',
          yAxisIndex: 1,
          data: evolution.map((item: any) => item.cumulative),
          itemStyle: {
            color: '#e74c3c'
          }
        }
      ]
    };
  }

  // Funcții helper
  getRoundDisplayName(): string {
    switch (this.currentRound) {
      case 'tur1_2024': return 'Tur 1 Alegeri Prezidențiale 2024';
      case 'tur2_2024': return 'Tur 2 Alegeri Prezidențiale 2024 (ANULAT)';
      case 'tur_activ': return 'Tur Activ';
      default: return 'Prezență la Vot';
    }
  }

  getLocationDisplayName(): string {
    return this.currentLocation === 'romania' ? 'România' : 'Străinătate';
  }

  formatNumber(num: number): string {
    if (!num && num !== 0) return '0';
    return num.toLocaleString('ro-RO');
  }

  formatPercentage(num: number): string {
    if (!num && num !== 0) return '0.0%';
    return `${num.toFixed(1)}%`;
  }

  // Paginare
  onPageChange(page: number): void {
    this.currentPage = page;
    this.loadPresenceData();
  }

  getPageNumbers(): number[] {
    if (!this.presenceData?.pagination) return [];
    
    const totalPages = this.presenceData.pagination.total_pages;
    const currentPage = this.presenceData.pagination.current_page;
    const pages: number[] = [];
    
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return pages;
  }

  getPresenceStatusMessage(): string {
    if (!this.presenceData?.general_stats) return '';
    
    const stats = this.presenceData.general_stats;
    
    if (this.currentRound === 'tur2_2024') {
      return 'Turul 2 al alegerilor prezidențiale a fost anulat.';
    }
    
    if (this.isLiveMode) {
      return `Prezența LIVE: ${this.formatNumber(stats.total_voters)} votanți (${this.formatPercentage(stats.participation_rate)})`;
    }
    
    return `Prezența finală: ${this.formatNumber(stats.total_voters)} votanți din ${this.formatNumber(stats.registered_permanent)} înscriși (${this.formatPercentage(stats.participation_rate)})`;
  }
}