from django.core.management.base import BaseCommand
from django.db import transaction
from news.models import Category, OpinionAuthor, Opinion, Poll, PollOption
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Populează modelele de opinii și sondaje cu date inițiale'

    def handle(self, *args, **options):
        self.stdout.write('Începe popularea modelelor de opinii și sondaje...')
        
        # Verifică existența categoriilor
        if not Category.objects.exists():
            self.stdout.write(self.style.ERROR('Nu există categorii. Rulează mai întâi comanda populate_categories.'))
            return
        
        # Obține categoriile
        categories = {}
        for category in Category.objects.all():
            categories[category.slug] = category
            
        # Verifică că avem categoriile necesare
        required_categories = ['elections', 'politics', 'technology', 'security']
        for slug in required_categories:
            if slug not in categories:
                self.stdout.write(self.style.ERROR(f'Categoria {slug} nu există. Rulează mai întâi comanda populate_categories.'))
                return
                
        self.stdout.write('Toate categoriile necesare există. Continuă popularea...')
        
        # ================ POPULARE AUTORI ================
        self.stdout.write('Creează autorii de opinii...')
        
        authors_data = [
            {
                'name': 'Dr. Maria Ionescu',
                'title': 'Expert în Securitate Cibernetică'
            },
            {
                'name': 'Prof. Alexandru Popescu',
                'title': 'Profesor de Științe Politice'
            },
            {
                'name': 'Andrei Dumitrescu',
                'title': 'Dezvoltator Software & Activist pentru Drepturi Digitale'
            },
            {
                'name': 'Elena Georgescu',
                'title': 'Cercetător în Sisteme Electorale'
            },
            {
                'name': 'Mihai Stanciu',
                'title': 'Consultant în Guvernare Electronică'
            }
        ]
        
        authors = {}
        with transaction.atomic():
            for author_data in authors_data:
                author, created = OpinionAuthor.objects.get_or_create(
                    name=author_data['name'],
                    defaults=author_data
                )
                authors[author.name] = author
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Autorul '{author.name}' a fost creat."))
                else:
                    self.stdout.write(self.style.WARNING(f"Autorul '{author.name}' există deja."))
                    
        # ================ POPULARE OPINII ================
        self.stdout.write('Creează opiniile...')
        
        opinions_data = [
            {
                'title': 'De ce votul electronic este viitorul democrației în România',
                'slug': 'de-ce-votul-electronic-este-viitorul-democratiei',
                'content': '''
                    În era digitală în care trăim, implementarea votului electronic în România reprezintă un pas esențial către modernizarea proceselor democratice.

                    În primul rând, votul electronic are potențialul de a crește semnificativ participarea la scrutine electorale. Unul dintre motivele principale pentru care mulți cetățeni nu participă la vot este dificultatea logistică - fie că sunt în altă localitate, fie că sunt în străinătate sau au dificultăți de mobilitate. Sistemul electronic ar elimina aceste bariere, permițând oricui să voteze de pe un dispozitiv conectat la internet.

                    În al doilea rând, votul electronic poate oferi rezultate aproape instantanee, eliminând procesele consumatoare de timp de numărare manuală și reducând semnificativ posibilitatea erorilor umane. Acest lucru ar crește încrederea în procesul electoral și ar reduce contestațiile bazate pe nereguli în numărarea voturilor.

                    În al treilea rând, deși există preocupări legitime legate de securitate, tehnologiile moderne precum blockchain și criptarea de ultimă generație pot asigura un nivel de securitate fără precedent. De fapt, un sistem electronic bine proiectat poate fi mai sigur decât metodele tradiționale, care sunt vulnerabile la fraudă prin "turism electoral", voturi multiple sau manipularea urnelor.

                    În concluzie, deși tranziția către votul electronic necesită investiții inițiale și o atenție deosebită la aspectele de securitate, beneficiile pe termen lung pentru democrația românească sunt incontestabile. Este timpul să ne aliniem cu țările care au implementat deja cu succes astfel de sisteme și să facem un pas decisiv către viitorul proceselor electorale.
                ''',
                'summary': 'Beneficiile implementării votului electronic în România - de la creșterea participării la vot până la rezultate mai rapide și mai exacte.',
                'publish_date': timezone.now() - datetime.timedelta(days=3),
                'author': authors['Dr. Maria Ionescu'],
                'category': categories.get('elections'),
                'is_published': True,
                'views_count': 78
            },
            {
                'title': 'Votul electronic: între oportunitate și vulnerabilitate',
                'slug': 'votul-electronic-intre-oportunitate-si-vulnerabilitate',
                'content': '''
                    Votul electronic reprezintă o oportunitate semnificativă pentru modernizarea sistemului electoral din România, însă implementarea sa trebuie abordată cu prudență și o înțelegere clară a potențialelor vulnerabilități.

                    Principalul avantaj al votului electronic este accesibilitatea. Cetățenii români din diaspora, cei cu mobilitate redusă sau cei care locuiesc în zone îndepărtate ar putea participa mai ușor la procesul democratic. De asemenea, tinerii, mai familiarizați cu tehnologia, ar putea fi mai înclinați să participe, crescând astfel prezența la vot în această categorie demografică.

                    Cu toate acestea, riscurile de securitate nu pot fi ignorate. Sistemele electronice pot fi vulnerabile la atacuri cibernetice sofisticate, care ar putea compromite integritatea alegerilor. Atacatorii ar putea încerca să modifice rezultatele, să blocheze accesul votanților sau să compromită confidențialitatea votului.

                    Un alt aspect esențial este transparența. Sistemele tradiționale de vot permit observatorilor să supravegheze fizic procesul electoral. În cazul votului electronic, acest nivel de transparență este mai greu de realizat, ceea ce poate genera neîncredere în rândul populației.

                    Pentru a implementa cu succes votul electronic în România, este necesară o abordare graduală. Sistemul ar trebui testat extensiv în alegeri locale sau referendum-uri înainte de a fi utilizat la nivel național. De asemenea, ar trebui să fie însoțit de măsuri robuste de securitate, inclusiv audit independent și posibilitatea verificării votului.

                    În concluzie, votul electronic poate reprezenta viitorul proceselor electorale în România, dar tranziția trebuie făcută cu atenție, prioritizând securitatea și transparența. Numai astfel putem beneficia de avantajele digitalizării fără a compromite fundamentele democrației.
                ''',
                'summary': 'O analiză echilibrată a oportunităților și riscurilor implementării votului electronic în contextul românesc actual.',
                'publish_date': timezone.now() - datetime.timedelta(days=5),
                'author': authors['Andrei Dumitrescu'],
                'category': categories.get('security'),
                'is_published': True,
                'views_count': 63
            },
            {
                'title': 'Tehnologia blockchain: fundamentul unui sistem de vot electronic securizat',
                'slug': 'tehnologia-blockchain-fundamentul-unui-sistem-de-vot-electronic-securizat',
                'content': '''
                    Tehnologia blockchain reprezintă una dintre cele mai promițătoare soluții pentru implementarea unui sistem de vot electronic securizat și transparent în România.

                    Blockchain-ul, cunoscut inițial ca tehnologia din spatele criptomonedelor, oferă câteva caracteristici esențiale pentru un sistem electoral digital: descentralizare, imutabilitate și transparență. Aceste atribute pot adresa multe dintre preocupările legate de securitatea și integritatea votului electronic.

                    Prin natura sa descentralizată, un sistem de vot bazat pe blockchain elimină punctele unice de eșec sau vulnerabilitate. Datele sunt stocate simultan pe multiple noduri, făcând practic imposibilă manipularea rezultatelor fără a compromite întreaga rețea - o sarcină extrem de dificilă din punct de vedere tehnic.

                    Imutabilitatea blockchain-ului înseamnă că odată ce un vot este înregistrat, nu poate fi modificat sau șters. Acest lucru oferă o garanție solidă împotriva fraudei electorale și permite auditarea completă a procesului electoral.

                    Transparența este asigurată prin posibilitatea verificării publice a tranzacțiilor (în acest caz, voturi), menținând în același timp anonimitatea votanților prin utilizarea cheilor criptografice. Fiecare votant ar putea verifica dacă votul său a fost înregistrat corect, fără a compromite secretul votului.

                    Există deja exemple de succes la nivel global. Estonia, una dintre țările pionier în e-guvernare, explorează implementarea blockchain-ului în sistemul său de vot electronic. De asemenea, proiecte pilot au fost desfășurate în Elveția și anumite state din SUA.

                    Pentru România, adoptarea unei soluții bazate pe blockchain ar putea reprezenta nu doar o modernizare a sistemului electoral, ci și un pas important către poziționarea țării ca un inovator în domeniul guvernării digitale. Este esențial, însă, ca implementarea să fie făcută gradual, cu teste riguroase și educarea publicului despre funcționalitatea și securitatea sistemului.

                    Concluzia mea este că blockchain-ul oferă fundamentul tehnologic solid necesar pentru un sistem de vot electronic de încredere, capabil să îmbunătățească semnificativ procesul democratic din România.
                ''',
                'summary': 'Cum poate tehnologia blockchain să revoluționeze sistemele de vot electronic, oferind securitate, transparență și verificabilitate.',
                'publish_date': timezone.now() - datetime.timedelta(days=7),
                'author': authors['Mihai Stanciu'],
                'category': categories.get('technology'),
                'is_published': True,
                'views_count': 92
            },
            {
                'title': 'Lecții din experiența estoniană pentru implementarea votului electronic în România',
                'slug': 'lectii-din-experienta-estoniana-pentru-implementarea-votului-electronic',
                'content': '''
                    Estonia este frecvent menționată ca un exemplu de succes în implementarea votului electronic, fiind prima țară din lume care a permis votul online la nivel național. Din experiența estoniană, România poate extrage lecții valoroase pentru propria sa tranziție către digitalizarea proceselor electorale.

                    Prima și cea mai importantă lecție este necesitatea unei infrastructuri digitale solide înainte de implementarea votului electronic. Estonia a început cu introducerea cărții de identitate electronice în 2002, mult înainte de primul vot electronic din 2005. Aceasta a permis autentificarea sigură a cetățenilor și a constituit baza tehnică pentru votul online. România ar trebui să accelereze implementarea și adoptarea cărții electronice de identitate înainte de a considera implementarea votului electronic la scară largă.

                    A doua lecție privește abordarea graduală. Estonia nu a implementat votul electronic brusc și universal. A început cu teste pilot, apoi a permis votul electronic ca opțiune suplimentară alături de metodele tradiționale. Această abordare incrementală a permis perfecționarea sistemului și construirea încrederii publice. România ar trebui să urmeze un traseu similar, începând poate cu alegeri locale sau referendum-uri.

                    A treia lecție se referă la transparența și auditabilitatea sistemului. Estonia a făcut public codul sursă al sistemului său de vot și a permis experților independenți să îl analizeze. Această transparență a fost esențială pentru a câștiga încrederea publicului și a experților în securitate.

                    De asemenea, Estonia a investit masiv în educația digitală a populației. Fără o populație familiarizată cu tehnologia, chiar și cel mai bun sistem de vot electronic ar avea o adoptare limitată. România trebuie să investească în programe de alfabetizare digitală, mai ales în zonele rurale și pentru persoanele în vârstă.

                    Nu în ultimul rând, Estonia a tratat securitatea cibernetică ca o prioritate națională. După atacurile cibernetice din 2007, țara a dezvoltat o strategie robustă de securitate și a creat unități specializate pentru protejarea infrastructurii digitale. România trebuie să dezvolte capabilități similare pentru a proteja viitorul sistem de vot electronic.

                    În concluzie, experiența Estoniei oferă un model valoros pentru România, dar contextul specific al țării noastre - nivelul de adoptare digitală, încrederea în instituții, infrastructura existentă - trebuie luat în considerare pentru a adapta acest model la realitățile locale.
                ''',
                'summary': 'Ce putem învăța din implementarea de succes a votului electronic în Estonia și cum putem adapta aceste lecții la contextul românesc.',
                'publish_date': timezone.now() - datetime.timedelta(days=9),
                'author': authors['Elena Georgescu'],
                'category': categories.get('politics'),
                'is_published': True,
                'views_count': 85
            },
            {
                'title': 'Cadrul legislativ necesar pentru implementarea votului electronic în România',
                'slug': 'cadrul-legislativ-necesar-pentru-implementarea-votului-electronic',
                'content': '''
                    Implementarea votului electronic în România necesită nu doar soluții tehnologice avansate, ci și un cadru legislativ solid și comprehensiv, care să reglementeze toate aspectele acestui proces.

                    În primul rând, este necesară modificarea Constituției României și a Legii electorale pentru a recunoaște explicit votul electronic ca metodă validă de exprimare a opțiunilor electorale. Articolul 36 din Constituție, care garantează dreptul la vot, ar trebui completat pentru a include și votul prin mijloace electronice.

                    O componentă esențială a cadrului legislativ ar trebui să fie reglementarea procesului de identificare și autentificare a alegătorilor. Legea ar trebui să stabilească standarde stricte pentru verificarea identității, posibil prin utilizarea cărții electronice de identitate, combinată cu factori suplimentari de autentificare (autentificare multi-factor).

                    De asemenea, legislația trebuie să garanteze secretul votului în mediul electronic, stabilind cerințe tehnice și proceduri care să asigure că nimeni nu poate asocia un vot cu identitatea alegătorului. Aici ar trebui incluse prevederi specifice privind criptarea datelor și separarea informațiilor de identificare de cele despre votul exprimat.

                    Un aspect critic care necesită reglementare este auditabilitatea sistemului. Legea ar trebui să impună mecanisme care să permită verificarea integrității procesului electoral, fără a compromite secretul votului. Aceasta ar putea include obligativitatea publicării codului sursă pentru revizuire publică și audit independent.

                    În plus, cadrul legislativ trebuie să abordeze aspecte precum: procedurile pentru situații de urgență (defecțiuni tehnice, atacuri cibernetice), accesibilitatea sistemului pentru persoanele cu dizabilități, perioada de vot electronic (posibil extinsă față de votul tradițional), și măsuri de prevenire a intimidării sau vânzării voturilor.

                    Nu în ultimul rând, legea ar trebui să stabilească instituțiile responsabile pentru implementarea, supravegherea și certificarea sistemului de vot electronic. Este esențial să existe o delimitare clară a responsabilităților și mecanisme de control reciproc între aceste instituții.

                    În concluzie, un cadru legislativ bine conceput, care să abordeze toate aceste aspecte, este fundația esențială pentru un sistem de vot electronic sigur, transparent și de încredere în România. Procesul de elaborare a acestui cadru ar trebui să implice nu doar parlamentari și experți juridici, ci și specialiști în securitate informatică, reprezentanți ai societății civile și experți electorali.
                ''',
                'summary': 'Analiză detaliată a modificărilor legislative necesare pentru implementarea și reglementarea votului electronic în România.',
                'publish_date': timezone.now() - datetime.timedelta(days=12),
                'author': authors['Prof. Alexandru Popescu'],
                'category': categories.get('politics'),
                'is_published': True,
                'views_count': 67
            }
        ]
        
        # Folosim transaction pentru a asigura integritatea datelor
        with transaction.atomic():
            opinions_created = 0
            opinions_existing = 0
            
            for opinion_data in opinions_data:
                # Curățăm conținutul
                opinion_data['content'] = opinion_data['content'].strip()
                
                # Verificăm dacă opinia există deja
                exists = Opinion.objects.filter(slug=opinion_data['slug']).exists()
                
                if exists:
                    self.stdout.write(self.style.WARNING(f"Opinia '{opinion_data['title']}' există deja."))
                    opinions_existing += 1
                    continue
                    
                # Creăm opinia
                Opinion.objects.create(**opinion_data)
                self.stdout.write(self.style.SUCCESS(f"Opinia '{opinion_data['title']}' a fost creată."))
                opinions_created += 1
                
            self.stdout.write(f"S-au creat {opinions_created} opinii noi și {opinions_existing} existau deja.")
            
        # ================ POPULARE SONDAJ ================
        self.stdout.write('Creează sondajul activ...')
        
        poll_data = {
            'question': 'Considerați că România este pregătită pentru implementarea votului electronic?',
            'is_active': True,
            'sample_size': 1200,
            'sample_date': timezone.now().date() - datetime.timedelta(days=15)
        }
        
        poll_options = [
            {'text': 'Da, este timpul pentru modernizare', 'votes': 780},
            {'text': 'Nu, mai sunt multe riscuri de rezolvat', 'votes': 420}
        ]
        
        with transaction.atomic():
            # Verificăm dacă există deja un sondaj cu aceeași întrebare
            existing_poll = Poll.objects.filter(question=poll_data['question']).first()
            
            if existing_poll:
                self.stdout.write(self.style.WARNING(f"Sondajul '{poll_data['question']}' există deja."))
                poll = existing_poll
            else:
                # Creăm sondajul
                poll = Poll.objects.create(**poll_data)
                self.stdout.write(self.style.SUCCESS(f"Sondajul '{poll.question}' a fost creat."))
            
            # Adăugăm opțiunile
            for option_data in poll_options:
                # Verificăm dacă opțiunea există
                existing_option = PollOption.objects.filter(poll=poll, text=option_data['text']).first()
                
                if existing_option:
                    self.stdout.write(self.style.WARNING(f"Opțiunea '{option_data['text']}' există deja pentru acest sondaj."))
                else:
                    option = PollOption.objects.create(poll=poll, **option_data)
                    self.stdout.write(self.style.SUCCESS(f"Opțiunea '{option.text}' a fost creată cu {option.votes} voturi."))
        
        self.stdout.write(self.style.SUCCESS('Popularea modelelor de opinii și sondaje a fost finalizată cu succes!'))