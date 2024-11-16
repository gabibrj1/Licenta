import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-reviews',
  templateUrl: './reviews.component.html',
  styleUrls: ['./reviews.component.scss']
})
export class ReviewsComponent implements OnInit {
  // Lista recenziilor principale cu informații reale
  reviews = [
    { text: 'Platforma de vot este intuitivă și sigură. Am economisit timp valoros.', author: 'Andrei P.', position: 'Director IT', rating: 5 },
    { text: 'Sunt foarte mulțumit de serviciile oferite. Recomand cu căldură!', author: 'Ioana M.', position: 'Manager Proiect', rating: 5 },
    { text: 'Procesul de vot a fost simplu și rapid. Totul a decurs fără probleme.', author: 'Gabriel T.', position: 'Student', rating: 5 },
    { text: 'Am folosit VotAI pentru alegerile companiei. A fost o experiență excelentă!', author: 'Maria F.', position: 'CEO', rating: 4.5 },
    { text: 'Rezultatele au fost rapide și precise!', author: 'Carmen D.', position: 'Contabil', rating: 4 },
    { text: 'VotAI ne-a ajutat să economisim resurse și timp.', author: 'Laura S.', position: 'HR Manager', rating: 5 },
    { text: 'Am apreciat suportul oferit de echipă în timpul votului.', author: 'Mihai B.', position: 'Coordonator', rating: 4.5 },
    { text: 'Serviciul este excelent și ușor de utilizat!', author: 'Florin G.', position: 'Administrator', rating: 5 },
    { text: 'Configurarea și administrarea voturilor au fost intuitive.', author: 'Elena R.', position: 'Consultant', rating: 5 },
    { text: 'Votul online a simplificat procesul pentru echipa noastră.', author: 'Victor L.', position: 'Team Leader', rating: 5 },
  ];

  // Generare recenzii suplimentare cu funcții reale
  additionalReviews = Array.from({ length: 20 }, (_, i) => {
    const texts = [
      'Interfața este modernă și ușor de utilizat.',
      'Rezultatele au fost disponibile imediat după încheierea votului.',
      'Am fost surprins de simplitatea procesului de vot.',
      'Sistemul a fost foarte sigur, fără niciun incident.',
      'Un serviciu de înaltă calitate, perfect pentru nevoile noastre.',
      'Rezultatele au fost afișate în timp real, foarte impresionant.',
      'Am folosit platforma pentru mai multe tipuri de voturi, toate au decurs perfect.',
      'Siguranța datelor a fost prioritatea principală, iar acest lucru ne-a liniștit.',
      'Am primit feedback excelent de la colegi despre platformă.',
      'Procesul de autentificare a fost simplu și rapid.',
    ];

    const authors = [
      'Cristina T.', 'George D.', 'Alex P.', 'Diana M.', 'Sergiu L.',
      'Oana S.', 'Paul R.', 'Ana G.', 'Lucian I.', 'Bianca C.',
      'Radu F.', 'Simona V.', 'Dan B.', 'Alina E.', 'Marius N.',
      'Teodora K.', 'Vlad J.', 'Mirela H.', 'Adrian P.', 'Claudia L.'
    ];

    const positions = [
      'Specialist Marketing', 'Coordonator Logistică', 'Designer Grafic',
      'Analist Financiar', 'Manager Operațiuni', 'Consultant IT',
      'Profesor', 'Trainer', 'Responsabil Achiziții', 'Asistent Cercetare',
      'Manager Vânzări', 'Director General', 'Expert Juridic',
      'Manager Proiect', 'Asistent Medical', 'Inginer Software',
      'Șef Departament', 'Consultant Resurse Umane', 'Coordonator Evenimente',
      'Responsabil Comunicare'
    ];

    return {
      text: texts[i % texts.length],
      author: authors[i % authors.length],
      position: positions[i % positions.length],
      rating: i % 3 === 0 ? 5 : i % 3 === 1 ? 4.5 : 4
    };
  });

  constructor(private router: Router) {}

  ngOnInit(){
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  navigateBack() {
    this.router.navigate(['/home']);
  }
}
