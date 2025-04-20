import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { SharedService } from '../services/shared.service';

@Component({
  selector: 'app-misiune',
  templateUrl: './misiune.component.html',
  styleUrl: './misiune.component.scss'
})
export class MisiuneComponent implements OnInit {
  // Definirea secțiunilor de misiune și viziune
  missionSections = [
    {
      title: 'Democratizarea procesului electoral',
      description: 'Facilitarea accesului la vot pentru toți cetățenii, indiferent de locație sau circumstanțe personale.',
      icon: 'fa-vote-yea',
      animation: 'fade-right'
    },
    {
      title: 'Creșterea participării civice',
      description: 'Încurajarea unei rate mai mari de participare la alegerile de toate nivelurile prin eliminarea barierelor tradiționale.',
      icon: 'fa-users',
      animation: 'fade-left'
    },
    {
      title: 'Securizarea procesului electoral',
      description: 'Asigurarea unui sistem de vot transparent, verificabil și protejat împotriva fraudelor prin tehnologii moderne.',
      icon: 'fa-shield-alt',
      animation: 'fade-right'
    },
    {
      title: 'Informarea cetățenilor',
      description: 'Oferirea accesului la informații complete, corecte și nepărtinitoare despre candidați și procese electorale.',
      icon: 'fa-info-circle',
      animation: 'fade-left'
    },
    {
      title: 'Accesibilitate pentru toți',
      description: 'Crearea unei platforme care să fie utilizabilă și accesibilă pentru persoanele cu dizabilități, oferind șanse egale de participare.',
      icon: 'fa-universal-access',
      animation: 'fade-right'
    }
  ];

  visionSections = [
    {
      title: 'Un sistem de vot modern pentru România',
      description: 'Transformarea procesului electoral din România într-un model de inovație și accesibilitate la nivel european.',
      icon: 'fa-flag',
      animation: 'fade-up'
    },
    {
      title: 'Platformă digitală civică permanentă',
      description: 'Dezvoltarea unei comunități digitale active care să mențină implicarea civică pe tot parcursul anului, nu doar în perioadele electorale.',
      icon: 'fa-calendar-alt',
      animation: 'fade-up'
    },
    {
      title: 'Transparență și încredere',
      description: 'Crearea unui sistem care să inspire încredere prin transparență totală și verificabilitate a voturilor.',
      icon: 'fa-handshake',
      animation: 'fade-up'
    },
    {
      title: 'Inovație continuă',
      description: 'Angajamentul de a evolua constant prin integrarea celor mai noi tehnologii de securitate și autentificare.',
      icon: 'fa-rocket',
      animation: 'fade-up'
    },
    {
      title: 'Educație civică extinsă',
      description: 'Formarea unei noi generații de cetățeni informați și implicați în procesele democratice.',
      icon: 'fa-graduation-cap',
      animation: 'fade-up'
    }
  ];

  values = [
    {
      title: 'Securitate',
      description: 'Protejarea integrității votului și a datelor personale este prioritatea noastră absolută.',
      icon: 'fa-lock'
    },
    {
      title: 'Accesibilitate',
      description: 'Servicii disponibile pentru toți cetățenii, indiferent de abilitățile tehnice sau fizice.',
      icon: 'fa-universal-access'
    },
    {
      title: 'Neutralitate',
      description: 'Menținem o poziție strict neutră față de toate partidele și candidații.',
      icon: 'fa-balance-scale'
    },
    {
      title: 'Transparență',
      description: 'Toate procesele sunt documentate și accesibile pentru verificare.',
      icon: 'fa-eye'
    },
    {
      title: 'Inovație responsabilă',
      description: 'Adoptăm tehnologii noi doar după testarea riguroasă a securității și fiabilității lor.',
      icon: 'fa-lightbulb'
    },
    {
      title: 'Implicare continuă',
      description: 'Încurajăm participarea civică activă dincolo de momentul votului.',
      icon: 'fa-hands-helping'
    }
  ];

  systemFeatures = [
    {
      title: 'Autentificare biometrică AI',
      description: 'Sistem avansat de recunoaștere facială pentru autentificare și monitorizare continuă a utilizatorului în timpul votului.',
      icon: 'fa-fingerprint'
    },
    {
      title: 'Verificare cu buletinul',
      description: 'Posibilitatea de logare rapidă și sigură prin scanarea buletinului, în locul introducerii manuale a datelor.',
      icon: 'fa-id-card'
    },
    {
      title: 'Geolocalizare inteligentă',
      description: 'Utilizarea geolocației pentru afișarea automată a candidaților locali relevanți, personalizând astfel experiența de vot.',
      icon: 'fa-map-marker-alt'
    },
    {
      title: 'Sisteme de vot personalizate',
      description: 'Crearea și gestionarea propriilor sisteme de vot pentru organizații, asociații sau comunități.',
      icon: 'fa-cogs'
    }
  ];

  constructor(
    private titleService: Title,
    private sharedService: SharedService
  ) { }

  ngOnInit(): void {
    this.titleService.setTitle('Misiune și Viziune | SmartVote');
    // Notificăm serviciul că pagina a fost încărcată
    this.sharedService.setPageLoaded(true);
  }

  // Metodă pentru scrollarea către secțiunea de viziune
  scrollToVision(): void {
    document.getElementById('vision-section')?.scrollIntoView({ behavior: 'smooth' });
  }

  // Metodă pentru scrollarea către secțiunea de valori
  scrollToValues(): void {
    document.getElementById('values-section')?.scrollIntoView({ behavior: 'smooth' });
  }
}