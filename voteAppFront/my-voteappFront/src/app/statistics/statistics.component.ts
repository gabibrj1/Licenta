import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { StatisticsService } from '../services/statistics.service';
import { interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss']
})
export class StatisticsComponent implements OnInit, OnDestroy {
  statisticsData: any = null;
  liveData: any = null;
  isLoading = true;
  error = '';
  
  // Parametri de control
  currentLocation = 'romania';
  currentRound = 'tur1_2024';
  isLiveMode = false;
  
  // Opțiuni pentru grafice
  ageChartOptions: any = {};
  genderChartOptions: any = {};
  environmentChartOptions: any = {};
  turnoutChartOptions: any = {};
  
  // Subscriptions pentru auto-refresh
  private refreshSubscription?: Subscription;
  
  constructor(
    private statisticsService: StatisticsService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    // Ascultă schimbările de parametri din rută
    this.route.queryParams.subscribe(params => {
      this.currentLocation = params['location'] || 'romania';
      this.currentRound = params['round'] || 'tur1_2024';
      
      this.isLiveMode = this.currentRound === 'tur_activ';
      
      this.loadStatistics();
      
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
  }

  loadStatistics(): void {
    this.isLoading = true;
    this.error = '';
    
    this.statisticsService.getVoteStatistics(this.currentLocation, this.currentRound)
      .subscribe({
        next: (data) => {
          this.statisticsData = data;
          this.setupCharts();
          this.isLoading = false;
        },
        error: (error) => {
          this.error = 'Eroare la încărcarea statisticilor: ' + (error.error?.message || error.message);
          this.isLoading = false;
        }
      });
  }

  startLiveUpdates(): void {
    // Actualizează la fiecare 30 de secunde în modul live
    this.refreshSubscription = interval(30000)
      .pipe(
        switchMap(() => this.statisticsService.getLiveStatistics())
      )
      .subscribe({
        next: (liveData) => {
          this.liveData = liveData;
          this.loadStatistics(); // Reîncarcă și statisticile generale
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

  setupCharts(): void {
    if (!this.statisticsData) return;

    this.setupAgeChart();
    this.setupGenderChart();
    this.setupEnvironmentChart();
    this.setupTurnoutChart();
  }

  setupAgeChart(): void {
    const ageData = this.statisticsData.age_distribution || [];
    
    this.ageChartOptions = {
      title: {
        text: 'Distribuția pe grupe de vârstă',
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
          name: 'Grupe de vârstă',
          type: 'pie',
          radius: '50%',
          data: ageData.map((item: any) => ({
            name: item.age_group,
            value: item.count
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    };
  }

  setupGenderChart(): void {
    const genderData = this.statisticsData.gender_distribution || [];
    
    this.genderChartOptions = {
      title: {
        text: 'Distribuția pe gen',
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
        orient: 'horizontal',
        bottom: 'bottom',
        textStyle: {
          color: '#ffffff'
        }
      },
      series: [
        {
          name: 'Gen',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          data: genderData.map((item: any) => ({
            name: item.gender_name,
            value: item.count
          })),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    };
  }

  setupEnvironmentChart(): void {
    const envData = this.statisticsData.environment_distribution || [];
    
    if (envData.length === 0) {
      this.environmentChartOptions = null;
      return;
    }
    
    this.environmentChartOptions = {
      title: {
        text: 'Distribuția pe mediu',
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
      xAxis: {
        type: 'category',
        data: envData.map((item: any) => item.environment_name),
        axisLabel: {
          color: '#ffffff'
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#ffffff'
        }
      },
      series: [
        {
          name: 'Numărul de voturi',
          type: 'bar',
          data: envData.map((item: any) => item.count),
          itemStyle: {
            color: function(params: any) {
              const colors = ['#3498db', '#2ecc71'];
              return colors[params.dataIndex % colors.length];
            }
          }
        }
      ]
    };
  }

  setupTurnoutChart(): void {
    const turnoutData = this.statisticsData.hourly_turnout || [];
    
    if (turnoutData.length === 0) {
      this.turnoutChartOptions = null;
      return;
    }
    
    this.turnoutChartOptions = {
      title: {
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
        data: ['Voturi per interval', 'Total cumulativ'],
        textStyle: {
          color: '#ffffff'
        }
      },
      xAxis: {
        type: 'category',
        data: turnoutData.map((item: any) => item.time),
        axisLabel: {
          color: '#ffffff',
          rotate: 45
        }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Voturi per interval',
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
          name: 'Voturi per interval',
          type: 'bar',
          data: turnoutData.map((item: any) => item.votes),
          itemStyle: {
            color: '#3498db'
          }
        },
        {
          name: 'Total cumulativ',
          type: 'line',
          yAxisIndex: 1,
          data: turnoutData.map((item: any) => item.cumulative),
          itemStyle: {
            color: '#e74c3c'
          }
        }
      ]
    };
  }

  getRoundDisplayName(): string {
    switch (this.currentRound) {
      case 'tur1_2024': return 'Tur 1 Alegeri Prezidențiale 2024';
      case 'tur2_2024': return 'Tur 2 Alegeri Prezidențiale 2024';
      case 'tur_activ': return 'Tur Activ';
      default: return 'Statistici Vot';
    }
  }
  getMostActiveAgeGroup(): string {
  if (!this.statisticsData?.age_distribution || this.statisticsData.age_distribution.length === 0) {
    return 'N/A';
  }
  
  const maxGroup = this.statisticsData.age_distribution.reduce((prev: any, current: any) => 
    (prev.count > current.count) ? prev : current
  );
  
  return `${maxGroup.age_group} (${maxGroup.percentage}%)`;
}

  getLocationDisplayName(): string {
    return this.currentLocation === 'romania' ? 'România' : 'Străinătate';
  }

  formatNumber(num: number): string {
    return num.toLocaleString('ro-RO');
  }
}