from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import date
from presidential_candidates.models import (
    PresidentialCandidate, ElectionYear, Controversy
)

class Command(BaseCommand):
    help = 'Populează baza de date cu controverse pentru candidații prezidențiali și asigură că toți anii electorali au controverse'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Începe popularea controverselor pentru candidații prezidențiali...'))

        # Lista de controverse pentru candidați
        controversies_data = [
            # Controverse pentru Crin Antonescu
            {
                'title': 'Retragerea lui Crin Antonescu din politică',
                'description': 'În 2014, Crin Antonescu s-a retras brusc din politică după rezultatele slabe la alegerile europarlamentare, '
                               'generând controverse și speculații despre motivele reale ale deciziei sale. '
                               'Revenirea sa în politică în 2024 a reactivat discuțiile despre această perioadă.',
                'date': date(2014, 5, 30),
                'candidate_name': 'Crin Antonescu',
                'election_year_value': 2024,
                'impact': 'Impact moderat asupra credibilității sale politice la revenirea în arena politică.'
            },
            {
                'title': 'Discursul controversat din campania prezidențială',
                'description': 'În timpul campaniei din 2024, Crin Antonescu a făcut declarații controversate despre perioada în care '
                               'a fost președinte interimar al României, minimizând importanța referendumului pentru demiterea lui Traian Băsescu din 2012.',
                'date': date(2024, 9, 15),
                'candidate_name': 'Crin Antonescu',
                'election_year_value': 2024,
                'impact': 'Impact redus, considerat o gafă de campanie, dar care a reactivat discuțiile despre perioada 2012.'
            },

            # Controverse pentru George Simion
            {
                'title': 'Interdicția de intrare în Republica Moldova',
                'description': 'George Simion a avut interdicție de a intra în Republica Moldova pentru mai mulți ani, '
                               'fiind acuzat de autoritățile moldovenești că ar fi fost implicat în activități care amenință securitatea națională. '
                               'Această situație a fost amplu discutată în timpul candidaturii sale prezidențiale.',
                'date': date(2018, 10, 1),
                'candidate_name': 'George Simion',
                'election_year_value': 2024,
                'impact': 'Impact major asupra imaginii sale în rândul diasporei moldovenești și a potențialilor alegători de centru.'
            },
            {
                'title': 'Incidentul din Parlament cu un deputat minoritar',
                'description': 'În timpul unui discurs în Parlament, George Simion a fost implicat într-un incident controversat '
                               'cu un deputat al minorităților naționale, ceea ce a generat acuzații de comportament extremist și intolerant.',
                'date': date(2022, 2, 7),
                'candidate_name': 'George Simion',
                'election_year_value': 2024,
                'impact': 'Impact semnificativ, consolidând percepția despre tendințele extremiste ale candidatului.'
            },

            # Controverse pentru Lavinia Șandru
            {
                'title': 'Reconversia din jurnalism în politică',
                'description': 'Trecerea Laviniei Șandru din jurnalism înapoi în politică a stârnit controverse '
                               'privind independența sa editorială în perioada în care a activat ca jurnalistă după cariera politică anterioară.',
                'date': date(2024, 6, 10),
                'candidate_name': 'Lavinia Șandru',
                'election_year_value': 2024,
                'impact': 'Impact moderat, afectând credibilitatea sa în ochii publicului care îi urmărise activitatea jurnalistică.'
            },
            {
                'title': 'Declarațiile controversate despre sistemul judiciar',
                'description': 'În timpul campaniei prezidențiale, Lavinia Șandru a făcut o serie de declarații controversate '
                               'despre sistemul judiciar din România, punând sub semnul întrebării independența magistraților.',
                'date': date(2024, 8, 20),
                'candidate_name': 'Lavinia Șandru',
                'election_year_value': 2024,
                'impact': 'Impact redus asupra campaniei sale, dar a generat critici din partea asociațiilor de magistrați.'
            },

            # Controverse pentru Nicușor Dan
            {
                'title': 'Conflictul de interese în cazul PUZ-urilor din București',
                'description': 'Nicușor Dan a fost acuzat de conflict de interese în legătură cu anularea unor Planuri Urbanistice Zonale '
                               'din București, după ce anterior, ca activist, inițiase procese împotriva acestora.',
                'date': date(2021, 3, 15),
                'candidate_name': 'Nicușor Dan',
                'election_year_value': 2024,
                'impact': 'Impact semnificativ asupra imaginii sale de administrator al Capitalei și potențial prezidențiabil.'
            },
            {
                'title': 'Controversa legată de infrastructura de termoficare',
                'description': 'Administrația condusă de Nicușor Dan a fost puternic criticată pentru gestionarea infrastructurii '
                               'de termoficare din București, în special în perioadele de iarnă, când numeroși bucureșteni au rămas fără căldură.',
                'date': date(2022, 1, 10),
                'candidate_name': 'Nicușor Dan',
                'election_year_value': 2024,
                'impact': 'Impact major asupra reputației sale ca administrator public, afectând credibilitatea candidaturii prezidențiale.'
            },

            # Controverse pentru Marcel Ciolacu
            {
                'title': 'Controversa tezei de doctorat',
                'description': 'În timpul campaniei prezidențiale, au apărut acuzații potrivit cărora teza de doctorat a lui Marcel Ciolacu '
                               'ar conține pasaje plagiate, reactivând o controversă mai veche din spațiul public.',
                'date': date(2024, 7, 5),
                'candidate_name': 'Marcel Ciolacu',
                'election_year_value': 2024,
                'impact': 'Impact moderat, similar cu controversele anterioare de plagiat din politica românească.'
            },
            {
                'title': 'Controversa "Ceaușescu avea dreptate"',
                'description': 'În timpul unui discurs, Marcel Ciolacu a afirmat că "Ceaușescu avea dreptate" referindu-se la '
                               'politica industrială, declarație care a generat controverse ample în spațiul public și acuzații de nostalgie comunistă.',
                'date': date(2023, 11, 20),
                'candidate_name': 'Marcel Ciolacu',
                'election_year_value': 2024,
                'impact': 'Impact semnificativ, fiind folosită intens de adversarii politici în campania electorală.'
            },

            # Controverse pentru Nicolae Ciucă
            {
                'title': 'Controversa tezei de doctorat plagiate',
                'description': 'Nicolae Ciucă a fost acuzat că și-a plagiat teza de doctorat, un scandal care a izbucnit '
                               'în perioada în care ocupa funcția de prim-ministru și a continuat în campania prezidențială.',
                'date': date(2022, 1, 18),
                'candidate_name': 'Nicolae Ciucă',
                'election_year_value': 2024,
                'impact': 'Impact semnificativ asupra credibilității sale academice și politice, afectând percepția publică.'
            },
            {
                'title': 'Discursurile generate de inteligența artificială',
                'description': 'În timpul campaniei prezidențiale, Nicolae Ciucă a fost acuzat că folosește inteligența artificială '
                               'pentru a-și genera discursurile și declarațiile politice, ridicând întrebări despre autenticitatea sa.',
                'date': date(2024, 8, 10),
                'candidate_name': 'Nicolae Ciucă',
                'election_year_value': 2024,
                'impact': 'Impact moderat, generând ironii în spațiul public și afectând percepția despre capacitățile sale de comunicare.'
            },

            # Controverse pentru Viorica Dăncilă
            {
                'title': 'Gafele de exprimare din timpul mandatului',
                'description': 'Viorica Dăncilă a fost intens criticată pentru numeroasele gafe de exprimare din perioada '
                               'în care a ocupat funcția de prim-ministru, acestea fiind readuse în discuție în timpul campaniei prezidențiale din 2019.',
                'date': date(2019, 9, 5),
                'candidate_name': 'Viorica Dăncilă',
                'election_year_value': 2019,
                'impact': 'Impact major asupra credibilității sale ca potențial președinte, fiind percepută ca nepregătită pentru funcție.'
            },
            {
                'title': 'Controversa legată de mutarea ambasadei din Israel',
                'description': 'În perioada în care era prim-ministru, Viorica Dăncilă a anunțat intenția de a muta ambasada României din Israel '
                               'la Ierusalim, contrar poziției președintelui și generând tensiuni diplomatice semnificative.',
                'date': date(2019, 3, 24),
                'candidate_name': 'Viorica Dăncilă',
                'election_year_value': 2019,
                'impact': 'Impact semnificativ, demonstrând lipsa de coordonare în politica externă și afectând credibilitatea internațională.'
            },

            # Controverse pentru Dan Barna
            {
                'title': 'Investigația Rise Project',
                'description': 'În timpul campaniei prezidențiale din 2019, Dan Barna a fost subiectul unei investigații jurnalistice '
                               'realizate de Rise Project privind proiectele cu fonduri europene pe care le-a gestionat înainte de a intra în politică.',
                'date': date(2019, 10, 15),
                'candidate_name': 'Dan Barna',
                'election_year_value': 2019,
                'impact': 'Impact major, fiind considerată una din cauzele pentru care nu a reușit să intre în turul doi al alegerilor.'
            },
            {
                'title': 'Declarația despre deținuții politici',
                'description': 'Dan Barna a stârnit controverse când a declarat că nu toți deținuții politici din perioada comunistă '
                               'au făcut închisoare pe nedrept, sugerând că unii meritau să fie condamnați pentru activitățile lor.',
                'date': date(2019, 11, 5),
                'candidate_name': 'Dan Barna',
                'election_year_value': 2019,
                'impact': 'Impact moderat, fiind folosită de adversarii politici pentru a-l acuza de lipsă de empatie și de cunoaștere istorică.'
            },

            # Controverse pentru Mircea Diaconu
            {
                'title': 'Conflictul de interese de la Teatrul Nottara',
                'description': 'Mircea Diaconu a fost implicat într-un scandal de conflict de interese legat de perioada '
                               'în care a condus Teatrul Nottara, caz care a ajuns în instanță și a fost readus în atenția '
                               'publicului în timpul campaniei prezidențiale din 2019.',
                'date': date(2019, 9, 20),
                'candidate_name': 'Mircea Diaconu',
                'election_year_value': 2019,
                'impact': 'Impact redus asupra campaniei, mulți alegători considerând cazul ca fiind o persecuție politică.'
            },
            {
                'title': 'Controversa legată de susținerea din partea ALDE și Pro România',
                'description': 'Deși a candidat ca independent, Mircea Diaconu a beneficiat de susținerea partidelor ALDE și Pro România, '
                               'ceea ce a generat acuzații că independența sa ar fi doar de fațadă, fiind de fapt candidatul acestor partide.',
                'date': date(2019, 8, 25),
                'candidate_name': 'Mircea Diaconu',
                'election_year_value': 2019,
                'impact': 'Impact moderat asupra credibilității sale ca independent autentic în ochii alegătorilor.'
            },

            # Controverse pentru Kelemen Hunor
            {
                'title': 'Declarațiile despre Trianon',
                'description': 'Kelemen Hunor a stârnit controverse cu declarațiile sale despre Tratatul de la Trianon, '
                               'sugerând că acesta reprezintă o tragedie pentru maghiari, ceea ce a generat reacții negative în spațiul public românesc.',
                'date': date(2019, 6, 4),
                'candidate_name': 'Kelemen Hunor',
                'election_year_value': 2019,
                'impact': 'Impact semnificativ în rândul electoratului românesc, consolidând percepția despre agenda sa pro-maghiară.'
            },
            {
                'title': 'Respingerea la intrarea în Ucraina',
                'description': 'În 2020, Kelemen Hunor a fost oprit la granița cu Ucraina și i s-a refuzat intrarea în țară pentru o perioadă, '
                               'incident care a generat tensiuni diplomatice și a reactivat discuțiile despre declarațiile sale controversate anterioare.',
                'date': date(2020, 10, 3),
                'candidate_name': 'Kelemen Hunor',
                'election_year_value': 2019,
                'impact': 'Impact moderat asupra imaginii sale, confirmând pentru unii alegători percepția de politician cu agenda separatistă.'
            },

            # Controverse pentru Theodor Stolojan
            {
                'title': 'Retragerea neașteptată din cursa prezidențială din 2004',
                'description': 'Theodor Stolojan s-a retras brusc din cursa prezidențială din 2004, fiind înlocuit de Traian Băsescu, '
                               'ceea ce a generat numeroase speculații și controverse privind motivele reale ale acestei decizii.',
                'date': date(2004, 10, 2),
                'candidate_name': 'Theodor Stolojan',
                'election_year_value': 2004,
                'impact': 'Impact major asupra carierei sale politice ulterioare, mulți considerând că a fost forțat să se retragă.'
            },
            {
                'title': 'Controversa legată de "statul paralel"',
                'description': 'În declarații publice, Theodor Stolojan a susținut existența unui "stat paralel" în România, '
                               'poziție care a generat controverse ample și l-a plasat în contradicție cu fostul său partid, PNL.',
                'date': date(2018, 6, 15),
                'candidate_name': 'Theodor Stolojan',
                'election_year_value': 2000,
                'impact': 'Impact moderat asupra credibilității sale politice, fiind perceput ca aliniat cu narațiunile PSD.'
            },

            # Controverse pentru Petre Roman
            {
                'title': 'Rolul în evenimentele din iunie 1990',
                'description': 'Petre Roman, în calitate de prim-ministru în timpul Mineriadei din iunie 1990, a fost acuzat '
                               'de complicitate la reprimarea violentă a manifestanților din Piața Universității, acuzații care l-au urmărit în toată cariera politică.',
                'date': date(1990, 6, 13),
                'candidate_name': 'Petre Roman',
                'election_year_value': 1996,
                'impact': 'Impact major asupra imaginii sale pe termen lung, afectând semnificativ șansele sale prezidențiale.'
            },
            {
                'title': 'Conflictul cu Ion Iliescu din 1991',
                'description': 'Conflictul deschis cu președintele Ion Iliescu care a dus la demiterea sa din funcția de prim-ministru '
                               'în septembrie 1991 a generat controverse privind stabilitatea politică a României post-comuniste.',
                'date': date(1991, 9, 26),
                'candidate_name': 'Petre Roman',
                'election_year_value': 1996,
                'impact': 'Impact semnificativ, consolidând imaginea sa de reformist, dar și de politician instabil în relațiile cu partenerii.'
            },

            # Controverse pentru Gheorghe Funar
            {
                'title': 'Politicile anti-maghiare din Cluj-Napoca',
                'description': 'În calitate de primar al municipiului Cluj-Napoca, Gheorghe Funar a implementat politici considerate anti-maghiare, '
                               'precum vopsirea băncilor, stâlpilor și bordurilor în culorile drapelului național, generând tensiuni interetnice.',
                'date': date(1992, 10, 15),
                'candidate_name': 'Gheorghe Funar',
                'election_year_value': 1992,
                'impact': 'Impact major asupra relațiilor interetnice din Transilvania și asupra imaginii internaționale a României.'
            },
            {
                'title': 'Teoriile controversate despre istoria dacilor',
                'description': 'Gheorghe Funar a promovat teorii istorice controversate despre originea dacilor și continuitatea daco-romană, '
                               'care au fost respinse de majoritatea istoricilor academici.',
                'date': date(1993, 5, 8),
                'candidate_name': 'Gheorghe Funar',
                'election_year_value': 1992,
                'impact': 'Impact moderat, consolidând imaginea sa de politician extremist și naționalist în ochii electoratului moderat.'
            },

            # Controverse pentru Radu Câmpeanu
            {
                'title': 'Acuzații de colaborare cu Securitatea',
                'description': 'Radu Câmpeanu a fost acuzat că ar fi colaborat cu Securitatea în perioada exilului său în Franța, '
                               'acuzații care au afectat semnificativ imaginea sa de disident anti-comunist autentic.',
                'date': date(1990, 4, 10),
                'candidate_name': 'Radu Câmpeanu',
                'election_year_value': 1990,
                'impact': 'Impact semnificativ asupra credibilității sale ca lider liberal și oponent al regimului comunist.'
            },
            {
                'title': 'Controversa legată de împărțirea PNL',
                'description': 'Sub conducerea lui Radu Câmpeanu, Partidul Național Liberal s-a fragmentat în mai multe facțiuni, '
                               'generând acuzații că ar fi contribuit la slăbirea opoziției democratice față de FSN-ul lui Ion Iliescu.',
                'date': date(1991, 3, 15),
                'candidate_name': 'Radu Câmpeanu',
                'election_year_value': 1990,
                'impact': 'Impact major asupra unității forțelor de dreapta în primii ani ai democrației post-comuniste.'
            },

            # Controverse pentru Ion Rațiu
            {
                'title': 'Controversa "Să moară şi capra vecinului"',
                'description': 'În timpul unei dezbateri televizate din campania din 1990, Ion Rațiu a folosit expresia "Să moară şi capra vecinului", '
                               'dorind să critice mentalitatea românească, dar fiind interpretat greșit ca promovând invidia socială.',
                'date': date(1990, 5, 10),
                'candidate_name': 'Ion Rațiu',
                'election_year_value': 1990,
                'impact': 'Impact moderat, generând o percepție negativă în rândul unui electorat nefamiliarizat cu stilul său occidental.'
            },
            {
                'title': 'Imaginea de "boier străin"',
                'description': 'Prezența sa elegantă, cu papion și maniere occidentale, i-a adus lui Ion Rațiu eticheta de "boier străin", '
                               'fiind perceput ca deconectat de realitățile românești după lungi ani de exil, imagine exploatată de adversarii politici.',
                'date': date(1990, 5, 5),
                'candidate_name': 'Ion Rațiu',
                'election_year_value': 1990,
                'impact': 'Impact semnificativ, contribuind la rezultatul electoral modest, în ciuda prestigiului său internațional.'
            },

            # Asigurăm că avem controverse pentru toți anii electorali
            # Controverse pentru 1992 (suplimentar)
            {
                'title': 'Manipularea rezultatelor alegerilor din 1992',
                'description': 'Opoziția a acuzat FDSN-ul lui Ion Iliescu de manipularea rezultatelor alegerilor prezidențiale din 1992, '
                               'în special în zonele rurale, unde controlul asupra procesului electoral era mai redus.',
                'date': date(1992, 9, 30),
                'election_year_value': 1992,
                'impact': 'Impact moderat asupra legitimității celui de-al doilea mandat al lui Ion Iliescu.'
            },

            # Controverse pentru 1996 (suplimentar)
            {
                'title': 'Dosarele de Securitate în campania din 1996',
                'description': 'În timpul campaniei prezidențiale din 1996 au apărut acuzații privind colaborarea unor candidați cu fosta Securitate, '
                               'generând dezbateri ample despre necesitatea lustrației și accesul la dosarele fostei poliții politice.',
                'date': date(1996, 10, 20),
                'election_year_value': 1996,
                'impact': 'Impact semnificativ, contribuind la victoria forțelor democratice și la prima alternanță la putere.'
            },

            # Controverse pentru 2019 (suplimentar)
            {
                'title': 'Organizarea defectuoasă a votului în diaspora în primul tur',
                'description': 'În primul tur al alegerilor prezidențiale din 2019 au existat probleme semnificative cu organizarea votului în diaspora, '
                               'cu cozi lungi și mulți români care nu au putut vota, generând proteste și acuzații la adresa guvernului PSD.',
                'date': date(2019, 11, 10),
                'election_year_value': 2019,
                'impact': 'Impact major, contribuind la mobilizarea masivă a diasporei în turul doi și la înfrângerea categorică a Vioricăi Dăncilă.'
            }
        ]

        # Adăugăm controversele în baza de date
        count_added = 0
        for controversy_data in controversies_data:
            # Extragem numele candidatului și anul electoral (dacă există)
            candidate_name = controversy_data.pop('candidate_name', None)
            election_year_value = controversy_data.pop('election_year_value', None)
            
            # Inițializăm referințele la candidat și an electoral
            candidate = None
            election_year = None
            
            # Căutăm candidatul în baza de date (dacă există)
            if candidate_name:
                try:
                    candidate = PresidentialCandidate.objects.get(name=candidate_name)
                except PresidentialCandidate.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Candidatul {candidate_name} nu există în baza de date.'))
            
            # Căutăm anul electoral în baza de date (dacă există)
            if election_year_value:
                try:
                    election_year = ElectionYear.objects.get(year=election_year_value)
                except ElectionYear.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Anul electoral {election_year_value} nu există în baza de date.'))
            
            # Verificăm dacă controversa există deja (după titlu și dată)
            existing_controversy = Controversy.objects.filter(
                title=controversy_data['title'],
                date=controversy_data['date']
            ).exists()
            
            if not existing_controversy:
                # Creăm controversa nouă
                Controversy.objects.create(
                    candidate=candidate,
                    election_year=election_year,
                    **controversy_data
                )
                count_added += 1
                self.stdout.write(self.style.SUCCESS(f'Controversa "{controversy_data["title"]}" a fost adăugată.'))
            else:
                self.stdout.write(self.style.WARNING(f'Controversa "{controversy_data["title"]}" există deja în baza de date.'))
        
        self.stdout.write(self.style.SUCCESS(f'Popularea controverselor a fost finalizată cu succes! Au fost adăugate {count_added} controverse noi.'))
        
        # Verificăm că toți anii electorali au cel puțin o controversă
        years_without_controversies = []
        for year in ElectionYear.objects.all():
            controversy_count = Controversy.objects.filter(election_year=year).count()
            if controversy_count == 0:
                years_without_controversies.append(year.year)
        
        if years_without_controversies:
            self.stdout.write(self.style.WARNING(f'ATENȚIE: Următorii ani electorali nu au controverse asociate: {years_without_controversies}'))
        else:
            self.stdout.write(self.style.SUCCESS('Toți anii electorali au cel puțin o controversă asociată.'))