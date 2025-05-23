import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ResultsService } from '../services/results.service';
import { interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-results',
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.scss']
})
export class ResultsComponent implements OnInit, OnDestroy {
  resultsData: any = null;
  liveData: any = null;
  isLoading = true;
  error = '';
  
  // Parametri de control
  currentLocation = 'romania';
  currentRound = 'tur1_2024';
  isLiveMode = false;
  
  // Pentru countdown
  timeRemaining = 0;
  countdownDisplay = '';
  
  // Pentru alegerile locale - selecția județului
  selectedCounty = '';
  availableCounties: string[] = [];
  
  // Opțiuni pentru grafice
  resultsChartOptions: any = {};
  progressChartOptions: any = {};
  
  // Subscriptions pentru auto-refresh
  private refreshSubscription?: Subscription;
  private countdownSubscription?: Subscription;
  
  constructor(
    private resultsService: ResultsService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    // Ascultă schimbările de parametri din rută
    this.route.queryParams.subscribe(params => {
      this.currentLocation = params['location'] || 'romania';
      this.currentRound = params['round'] || 'tur1_2024';
      
      this.isLiveMode = this.currentRound === 'tur_activ';
      
      this.loadResults();
      
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

  loadResults(): void {
    this.isLoading = true;
    this.error = '';
    
    this.resultsService.getVoteResults(this.currentLocation, this.currentRound)
      .subscribe({
        next: (data) => {
          this.resultsData = data;
          this.updateAvailableCounties();
          this.setupCharts();
          this.setupCountdown();
          this.isLoading = false;
        },
        error: (error) => {
          this.error = 'Eroare la încărcarea rezultatelor: ' + (error.error?.message || error.message);
          this.isLoading = false;
        }
      });
  }

  startLiveUpdates(): void {
    // Actualizează la fiecare 15 secunde în modul live
    this.refreshSubscription = interval(15000)
      .pipe(
        switchMap(() => this.resultsService.getLiveResults())
      )
      .subscribe({
        next: (liveData) => {
          this.liveData = liveData;
          this.timeRemaining = liveData.time_remaining || 0;
          this.loadResults(); // Reîncarcă și rezultatele generale
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
    if (!this.resultsData) return;

    this.setupResultsChart();
    this.setupProgressChart();
  }

  setupResultsChart(): void {
    if (!this.resultsData.results || this.resultsData.results.length === 0) {
      this.resultsChartOptions = null;
      return;
    }

    const voteType = this.resultsData.round_info.vote_type;
    
    if (voteType === 'locale') {
      this.setupLocalResultsChart();
    } else {
      this.setupNationalResultsChart();
    }
  }

  setupNationalResultsChart(): void {
    const results = this.resultsData.results;
    const voteType = this.resultsData.round_info.vote_type;
    
    // Preparăm datele pentru grafic
    const chartData = results.map((result: any) => {
      let name = '';
      if (voteType === 'parlamentare') {
        name = `${result.abbreviation} - ${result.party_name}`;
      } else {
        name = `${result.candidate_name} (${result.party || 'Independent'})`;
      }
      
      return {
        name: name,
        value: result.votes,
        percentage: result.percentage
      };
    });

    this.resultsChartOptions = {
      title: {
        text: this.getChartTitle(),
        left: 'center',
        textStyle: {
          color: '#ffffff',
          fontSize: 16
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} voturi ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: {
          color: '#ffffff',
          fontSize: 10
        },
        formatter: (name: string) => {
          if (name.length > 25) {
            return name.substring(0, 25) + '...';
          }
          return name;
        }
      },
      series: [
        {
          name: 'Voturi',
          type: 'pie',
          radius: ['30%', '70%'],
          center: ['60%', '50%'],
          data: chartData,
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

  setupLocalResultsChart(): void {
    if (!this.resultsData.results || this.resultsData.results.length === 0) {
      this.resultsChartOptions = null;
      return;
    }

    // Folosește județul selectat sau primul județ disponibil
    let selectedCountyData = this.resultsData.results[0];
    
    if (this.selectedCounty) {
      const countyData = this.resultsData.results.find((county: any) => county.county === this.selectedCounty);
      if (countyData) {
        selectedCountyData = countyData;
      }
    }

    const chartData = selectedCountyData.candidates.map((candidate: any) => ({
      name: `${candidate.candidate_name} (${candidate.party || 'Independent'})`,
      value: candidate.votes,
      percentage: candidate.percentage
    }));

    this.resultsChartOptions = {
      title: {
        text: `Rezultate ${selectedCountyData.county}`,
        left: 'center',
        textStyle: {
          color: '#ffffff',
          fontSize: 16
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} voturi ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: {
          color: '#ffffff',
          fontSize: 10
        }
      },
      series: [
        {
          name: 'Voturi',
          type: 'pie',
          radius: ['30%', '70%'],
          center: ['60%', '50%'],
          data: chartData,
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

  setupProgressChart(): void {
    const progressData = this.resultsData.vote_progression || [];
    
    if (progressData.length === 0) {
      this.progressChartOptions = null;
      return;
    }
    
    this.progressChartOptions = {
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
        data: ['Voturi noi', 'Total cumulativ'],
        textStyle: {
          color: '#ffffff'
        }
      },
      xAxis: {
        type: 'category',
        data: progressData.map((item: any) => item.time),
        axisLabel: {
          color: '#ffffff',
          rotate: 45
        }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Voturi noi',
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
          name: 'Voturi noi',
          type: 'bar',
          data: progressData.map((item: any) => item.votes),
          itemStyle: {
            color: '#3498db'
          }
        },
        {
          name: 'Total cumulativ',
          type: 'line',
          yAxisIndex: 1,
          data: progressData.map((item: any) => item.cumulative),
          itemStyle: {
            color: '#e74c3c'
          }
        }
      ]
    };
  }

  getChartTitle(): string {
    const voteType = this.resultsData.round_info.vote_type;
    if (voteType === 'parlamentare') {
      return 'Rezultate Alegeri Parlamentare';
    } else if (voteType === 'prezidentiale_tur2') {
      return 'Rezultate Alegeri Prezidențiale - Turul 2';
    } else {
      return 'Rezultate Alegeri Prezidențiale';
    }
  }

  getRoundDisplayName(): string {
    switch (this.currentRound) {
      case 'tur1_2024': return 'Tur 1 Alegeri Prezidențiale 2024';
      case 'tur2_2024': return 'Tur 2 Alegeri Prezidențiale 2024';
      case 'tur_activ': return 'Tur Activ';
      default: return 'Rezultate Vot';
    }
  }

  getLocationDisplayName(): string {
    return this.currentLocation === 'romania' ? 'România' : 'Străinătate';
  }

  formatNumber(num: number): string {
    return num.toLocaleString('ro-RO');
  }

  getWinnerMessage(): string {
    if (!this.resultsData?.winner) {
      return 'Încă nu s-a determinat câștigătorul';
    }

    const winner = this.resultsData.winner;
    if (winner.type === 'candidate') {
      return `Câștigător: ${winner.name} (${winner.party}) cu ${this.formatNumber(winner.votes)} voturi (${winner.percentage}%)`;
    } else if (winner.type === 'party') {
      return `Câștigător: ${winner.name} (${winner.abbreviation}) cu ${this.formatNumber(winner.votes)} voturi (${winner.percentage}%)`;
    }

    return 'Rezultate în curs de procesare';
  }

  getTopResults(count: number = 5): any[] {
    if (!this.resultsData?.results) return [];
    
    if (this.resultsData.round_info.vote_type === 'locale') {
      // Pentru locale, returnăm candidații din județul selectat sau primul județ
      let selectedCountyData = this.resultsData.results[0];
      
      if (this.selectedCounty) {
        const countyData = this.resultsData.results.find((county: any) => county.county === this.selectedCounty);
        if (countyData) {
          selectedCountyData = countyData;
        }
      }
      
      return selectedCountyData?.candidates?.slice(0, count) || [];
    }
    
    return this.resultsData.results.slice(0, count);
  }

  updateAvailableCounties(): void {
    if (this.resultsData?.round_info?.vote_type === 'locale' && this.resultsData.results) {
      this.availableCounties = this.resultsData.results.map((county: any) => county.county);
      
      // Setează primul județ ca implicit dacă nu e selectat deja unul
      if (!this.selectedCounty && this.availableCounties.length > 0) {
        this.selectedCounty = this.availableCounties[0];
      }
    } else {
      this.availableCounties = [];
      this.selectedCounty = '';
    }
  }

  onCountyChange(): void {
    // Regenerează graficul când se schimbă județul
    if (this.resultsData?.round_info?.vote_type === 'locale') {
      this.setupLocalResultsChart();
    }
  }

  getPositionInRomanian(position: string): string {
    const positionMap: { [key: string]: string } = {
      'mayor': 'Primar',
      'primar': 'Primar',
      'consilier_local': 'Consilier Local',
      'councilor': 'Consilier Local',
      'local_councilor': 'Consilier Local',
      'consilier_judetean': 'Consilier Județean',
      'county_councilor': 'Consilier Județean',
      'presedinte_cj': 'Președinte Consiliu Județean',
      'county_president': 'Președinte Consiliu Județean'
    };
    
    return positionMap[position] || position;
  }
}