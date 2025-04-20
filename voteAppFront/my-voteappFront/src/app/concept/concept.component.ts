import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';

@Component({
  selector: 'app-concept',
  templateUrl: './concept.component.html',
  styleUrls: ['./concept.component.scss']
})
export class ConceptComponent implements OnInit {
  // Definirea principiilor arhitecturale
  architecturalPrinciples = [
    {
      title: 'Securitate prin design',
      description: 'Securitatea este integrată în fiecare aspect al sistemului, de la autentificare biometrică până la criptarea end-to-end a voturilor.',
      icon: '🔒'
    },
    {
      title: 'Transparență verificabilă',
      description: 'Procesul electoral este complet transparent și verificabil, permițând observatorilor să confirme corectitudinea fără a compromite anonimitatea votanților.',
      icon: '👁️'
    },
    {
      title: 'Accesibilitate universală',
      description: 'Sistemul este proiectat pentru a fi utilizabil de toți cetățenii, indiferent de nivelul de expertiză tehnică sau abilități.',
      icon: '♿'
    },
    {
      title: 'Flexibilitate și scalabilitate',
      description: 'Arhitectura sistemului permite adaptarea pentru diferite tipuri de alegeri și extinderea pentru a gestiona un număr mare de utilizatori.',
      icon: '📈'
    }
  ];

  // Tehnologii utilizate
  technologiesUsed = [
    {
      category: 'Frontend',
      items: [
        {
          name: 'Angular',
          description: 'Framework modern pentru dezvoltarea interfețelor utilizator dinamice și responsive'
        },
        {
          name: 'HTML5/CSS3/SCSS',
          description: 'Tehnologii standard pentru construirea și stilizarea interfeței utilizator'
        },
        {
          name: 'Biblioteci JavaScript',
          description: 'Pentru vizualizare de date, diagrame interactive și experiență utilizator îmbunătățită'
        }
      ]
    },
    {
      category: 'Backend',
      items: [
        {
          name: 'Django & Python',
          description: 'Framework robust și secure pentru dezvoltarea backend-ului'
        },
        {
          name: 'MySQL',
          description: 'Sistem de baze de date relațional pentru stocarea datelor în mod securizat'
        },
        {
          name: 'APIs RESTful',
          description: 'Arhitectură bazată pe API-uri pentru comunicarea eficientă între client și server'
        }
      ]
    },
    {
      category: 'Securitate',
      items: [
        {
          name: 'Criptografie avansată',
          description: 'Algoritmi de criptare moderni pentru protejarea datelor sensibile și a voturilor'
        },
        {
          name: 'Autentificare multi-factor',
          description: 'Combinație de metode de autentificare pentru securitate maximă, inclusiv recunoaștere facială'
        },
        {
          name: 'JWT & Token-uri',
          description: 'Sistem de autentificare bazat pe token-uri pentru sesiuni sigure și verificabile'
        }
      ]
    },
    {
      category: 'Inteligență Artificială',
      items: [
        {
          name: 'Computer Vision (YOLO)',
          description: 'Pentru scanarea buletinelor de identitate și extragerea automată a informațiilor'
        },
        {
          name: 'Recunoaștere Facială',
          description: 'Implementată pentru autentificarea sigură și verificarea identității în timpul votului'
        },
        {
          name: 'Algoritmi de Machine Learning',
          description: 'Pentru identificarea secțiilor de vot și optimizarea experienței utilizatorilor'
        }
      ]
    }
  ];

  // Procesul electoral
  electoralProcess = [
    {
      stage: 'Înregistrare și Verificare',
      description: 'Utilizatorii se înregistrează cu documente de identitate verificate prin scanare și recunoaștere facială.',
      steps: [
        'Scanarea documentului de identitate',
        'Verificarea autenticității documentului cu AI',
        'Autentificarea biometrică prin recunoaștere facială',
        'Confirmarea eligibilității pentru vot'
      ]
    },
    {
      stage: 'Pregătirea pentru Vot',
      description: 'Sistemul furnizează informații despre candidați și procesul electoral, pregătind alegătorul pentru decizia informată.',
      steps: [
        'Acces la informații despre candidați',
        'Familiarizare cu interfața de vot',
        'Simulare pentru înțelegerea procesului de vot',
        'Accesarea secției de votare virtuale'
      ]
    },
    {
      stage: 'Procesul de Vot',
      description: 'Votarea propriu-zisă se desfășoară într-un mediu securizat cu verificare continuă a identității.',
      steps: [
        'Autentificarea în sistem',
        'Verificarea continuă a identității prin monitorizare video',
        'Selectarea candidaților preferați',
        'Revizuirea și confirmarea opțiunilor'
      ]
    },
    {
      stage: 'Verificare și Confirmare',
      description: 'După votare, utilizatorul primește o confirmare unică și poate verifica includerea votului în totalul final.',
      steps: [
        'Generarea unui token unic de verificare',
        'Primirea confirmării prin email în format PDF',
        'Posibilitatea verificării ulterioare a votului',
        'Garanția anonimității corelată cu verificabilitatea'
      ]
    }
  ];

  constructor(private titleService: Title) { }

  ngOnInit(): void {
    this.titleService.setTitle('Concept Tehnic | SmartVote');
  }

  scrollToTechnologies(): void {
    document.getElementById('technologies-section')?.scrollIntoView({ behavior: 'smooth' });
  }

  scrollToProcess(): void {
    document.getElementById('process-section')?.scrollIntoView({ behavior: 'smooth' });
  }
}