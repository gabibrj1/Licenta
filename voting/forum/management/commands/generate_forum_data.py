import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction
from django.contrib.auth import get_user_model

from forum.models import Category, Topic, Post, Reaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Generează date de test pentru forum'

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            type=int,
            default=5,
            help='Numărul de categorii de generat'
        )
        parser.add_argument(
            '--topics',
            type=int,
            default=20,
            help='Numărul de subiecte de generat per categorie'
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=10,
            help='Numărul maxim de postări de generat per subiect'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Șterge datele existente înainte de a genera altele noi'
        )

    def handle(self, *args, **options):
        num_categories = options['categories']
        num_topics = options['topics']
        num_posts = options['posts']
        clear_data = options['clear']
        
        with transaction.atomic():
            # Verifică dacă există utilizatori în sistem
            users = list(User.objects.all())
            if not users:
                self.stdout.write(self.style.ERROR('Nu există utilizatori în sistem. Creați utilizatori înainte de a genera date pentru forum.'))
                return
                
            # Șterge datele existente dacă opțiunea este activată
            if clear_data:
                self.stdout.write('Ștergerea datelor existente...')
                Post.objects.all().delete()
                Topic.objects.all().delete()
                Category.objects.all().delete()
                
            # Generare categorii
            self.stdout.write('Generare categorii...')
            categories = self.generate_categories(num_categories)
            
            # Generare subiecte și postări
            self.stdout.write('Generare subiecte și postări...')
            for category in categories:
                self.generate_topics(category, num_topics, num_posts, users)
            
            self.stdout.write(self.style.SUCCESS(f'Date generate cu succes: {num_categories} categorii, aproximativ {num_categories * num_topics} subiecte'))

    def generate_categories(self, num_categories):
        """Generează categorii de forum"""
        # Definirea unor categorii predefinite
        predefined_categories = [
            {
                'name': 'Anunțuri Oficiale',
                'description': 'Anunțuri oficiale despre platforma de vot și actualizări importante',
                'icon': 'fa-bullhorn',
                'color': '#e74c3c'
            },
            {
                'name': 'Sisteme de Vot',
                'description': 'Discuții despre sistemele de vot disponibile și funcționalitățile acestora',
                'icon': 'fa-check-square',
                'color': '#3498db'
            },
            {
                'name': 'Securitate Electorală',
                'description': 'Discuții despre securitatea votului electronic și tehnologii de protecție',
                'icon': 'fa-shield-alt',
                'color': '#2ecc71'
            },
            {
                'name': 'Întrebări și Asistență',
                'description': 'Ajutor și asistență pentru utilizarea platformei SmartVote',
                'icon': 'fa-question-circle',
                'color': '#f39c12'
            },
            {
                'name': 'Feedback și Sugestii',
                'description': 'Oferă feedback și sugestii pentru îmbunătățirea platformei',
                'icon': 'fa-comment-dots',
                'color': '#9b59b6'
            },
            {
                'name': 'Experiențe de Vot',
                'description': 'Împărtășiți experiențele voastre cu utilizarea sistemelor de vot electronice',
                'icon': 'fa-user-check',
                'color': '#1abc9c'
            },
            {
                'name': 'Discuții Generale',
                'description': 'Discuții generale despre votul electronic și democrație',
                'icon': 'fa-comments',
                'color': '#34495e'
            },
        ]
        
        categories = []
        
        # Creează categoriile predefinite
        for i, category_data in enumerate(predefined_categories[:num_categories]):
            slug = slugify(category_data['name'])
            
            # Verifică dacă categoria există deja
            if not Category.objects.filter(slug=slug).exists():
                category = Category.objects.create(
                    name=category_data['name'],
                    slug=slug,
                    description=category_data['description'],
                    icon=category_data['icon'],
                    color=category_data['color'],
                    order=i
                )
                categories.append(category)
            else:
                # Dacă există, o returnăm
                categories.append(Category.objects.get(slug=slug))
        
        # Dacă sunt necesare mai multe categorii, generăm unele generice
        if num_categories > len(predefined_categories):
            for i in range(len(predefined_categories), num_categories):
                name = f'Categoria {i+1}'
                slug = slugify(name)
                
                if not Category.objects.filter(slug=slug).exists():
                    category = Category.objects.create(
                        name=name,
                        slug=slug,
                        description=f'O categorie generată pentru discuții diverse #{i+1}',
                        icon='fa-folder',
                        color='#7f8c8d',
                        order=i
                    )
                    categories.append(category)
                else:
                    categories.append(Category.objects.get(slug=slug))
        
        return categories

    def generate_topics(self, category, num_topics, num_posts, users):
        """Generează subiecte pentru o categorie"""
        # Definirea unor titluri de subiecte predefinite pentru fiecare categorie
        category_topics = {
            'anunțuri-oficiale': [
                'Actualizare platformă: Versiunea 2.0 cu suport pentru vot parlamentar',
                'Detalii importante despre securitatea votului în SmartVote',
                'Actualizare sistem: Îmbunătățiri la modulul de recunoaștere facială',
                'Anunț: Noua funcționalitate de vot personalizat disponibilă',
                'Informații despre procesul de verificare a identității'
            ],
            'sisteme-de-vot': [
                'Cum funcționează votul prezidențial în SmartVote?',
                'Diferențe între votul parlamentar și cel prezidențial',
                'Tutorial: Crearea unui sistem de vot personalizat',
                'Integrarea sistemului SmartVote cu aplicații externe',
                'Opțiuni de configurare pentru sistemele de vot personalizate'
            ],
            'securitate-electorală': [
                'Implementarea criptării end-to-end în SmartVote',
                'Cum detectează SmartVote tentativele de fraudă?',
                'Protecția datelor personale în procesul de vot electronic',
                'Analiza de securitate a sistemului de recunoaștere facială',
                'Comparație între diferite metode de autentificare pentru vot'
            ],
            'întrebări-și-asistență': [
                'Cum îmi pot recupera contul dacă am pierdut accesul?',
                'Probleme la scanarea buletinului - soluții și alternative',
                'Pot vota de pe dispozitive mobile?',
                'Ce fac dacă camera nu funcționează în timpul verificării?',
                'De ce nu pot crea un sistem de vot personalizat?'
            ],
            'feedback-și-sugestii': [
                'Propunere: Îmbunătățirea interfeței pentru persoane cu dizabilități',
                'Sugestie pentru implementarea unui sistem de recompense',
                'Feedback privind experiența utilizării pe dispozitive mobile',
                'Idei pentru extinderea opțiunilor de configurare a voturilor',
                'Sugestii pentru îmbunătățirea procesului de verificare'
            ],
            'experiențe-de-vot': [
                'Prima mea experiență cu votul electronic - ce am învățat',
                'Cum am organizat un vot pentru asociația de locatari',
                'Experiența organizării alegerilor studențești cu SmartVote',
                'Comparație între experiența de vot tradițional și electronic',
                'Feedback după utilizarea sistemului în alegeri locale'
            ],
            'discuții-generale': [
                'Viitorul votului electronic în România',
                'Impactul tehnologiei în procesele democratice',
                'Dezbateri privind securitatea versus accesibilitatea votului',
                'Aspecte legale ale implementării votului electronic',
                'Studii de caz: Votul electronic în alte țări'
            ]
        }
        
        # Listă generică de titluri pentru categorii care nu au predefinite
        generic_topics = [
            'Întrebare despre funcționalitatea sistemului',
            'Ajutor necesar pentru configurare',
            'Cum pot rezolva această problemă?',
            'Opinie despre îmbunătățirile recente',
            'Propunere de schimbare pentru platformă',
            'Experiența mea cu SmartVote',
            'Tutorial: cum să utilizați eficient sistemul',
            'Comparație între SmartVote și alte sisteme',
            'Dezbateri despre procesele electorale moderne',
            'Idei pentru viitoare actualizări'
        ]
        
        # Conținut pentru postările inițiale
        topic_contents = [
            'Bună ziua tuturor! Am dori să discutăm despre acest subiect important. Ce părere aveți despre această funcționalitate? Așteptăm părerea voastră și sugestii pentru îmbunătățiri viitoare.',
            
            'Salutare comunitate SmartVote! Recent am descoperit această funcționalitate și vreau să împart experiența mea cu voi. \n\nAm observat că sistemul este foarte intuitiv și ușor de folosit, dar am întâmpinat câteva dificultăți când am încercat să... \n\nCe experiențe ați avut voi? Cum credeți că ar putea fi îmbunătățit?',
            
            'Bună tuturor, \n\nAș dori să deschid o discuție despre importanța securității în sistemele de vot electronice. În urma cercetărilor recente, am observat că există mai multe abordări pentru asigurarea integrității votului: \n\n1. Criptarea end-to-end \n2. Verificarea în mai multe etape \n3. Auditul transparent \n\nCare credeți că este cea mai eficientă metodă? Aș aprecia orice opinie sau experiență relevantă.',
            
            'Vă salut! Sunt nou în comunitatea SmartVote și aș dori să înțeleg mai bine cum funcționează procesul de verificare a identității. Am încercat să urmez pașii din ghid, dar am întâmpinat o problemă la etapa de scanare a buletinului. \n\nCamera mea pare să funcționeze corect în alte aplicații, dar aici nu reușește să detecteze corect documentul. A mai întâmpinat cineva această problemă? Există vreo soluție?',
            
            'Dragă comunitate, \n\nVin cu o propunere pentru îmbunătățirea platformei bazată pe experiența mea recentă de organizare a unui vot intern pentru asociația noastră. Cred că ar fi foarte util să avem posibilitatea de a... \n\nCe părere aveți despre această idee? Ar fi utilă și pentru alți utilizatori?',
            
            'Salutare tuturor! \n\nAm organizat recent un vot folosind SmartVote și sunt impresionat de eficiența sistemului. Procesul a fost mult mai rapid decât metodele tradiționale și am apreciat în mod deosebit funcționalitatea de monitorizare în timp real. \n\nO sugestie de îmbunătățire ar fi adăugarea unor opțiuni mai avansate pentru raportare post-vot. \n\nCe alte funcționalități credeți că ar fi utile pentru organizatori?',
            
            'Bună ziua! \n\nAm o întrebare tehnică legată de integrarea API-ului SmartVote cu alte sisteme. Am încercat să folosesc documentația disponibilă, dar nu sunt sigur dacă înțeleg corect procesul de autentificare. \n\nCineva care a implementat deja o astfel de integrare ar putea să împărtășească experiența sa? Mulțumesc anticipat!',
            
            'Salut comunitate! \n\nSunt curios ce părere aveți despre implementarea votului electronic la scară largă în România. Care credeți că sunt principalele obstacole și cum ar putea fi depășite? \n\nPersonal, cred că educația digitală și încrederea publicului sunt factori critici. Ce ziceți?',
            
            'Bună tuturor, \n\nVreau să împărtășesc o experiență recentă cu sistemul de vot personalizat. Am creat un sondaj pentru grupul meu de prieteni și am fost plăcut surprins de cât de ușor a fost să configurez opțiunile și să distribui invitațiile. \n\nSingurul aspect care ar putea fi îmbunătățit este... \n\nCe experiențe ați avut voi cu această funcționalitate?',
            
            'Bună ziua, \n\nAș dori să discut despre accesibilitatea platformei pentru persoanele cu dizabilități. Am observat că interfața actuală ar putea prezenta dificultăți pentru utilizatorii cu deficiențe vizuale. \n\nExistă planuri pentru implementarea unor funcționalități de accesibilitate suplimentare? Ce recomandări ați avea pentru îmbunătățirea experienței acestor utilizatori?'
        ]
        
        # Conținut pentru răspunsuri
        reply_contents = [
            'Mulțumesc pentru postare! Sunt de acord cu punctul tău de vedere și aș adăuga că...',
            
            'Interesantă perspectivă! În experiența mea, am observat că această abordare funcționează cel mai bine când...',
            
            'Nu sunt sigur că sunt de acord. Din ce am observat eu, ar fi mai eficient să...',
            
            'Excelent punct de vedere! Ai putea să detaliezi puțin mai mult despre...?',
            
            'Am întâmpinat și eu aceeași problemă. Soluția pe care am găsit-o a fost să...',
            
            'Mulțumesc pentru împărtășirea experienței tale! Este foarte util să auzim perspective diverse.',
            
            'Interesant subiect! Aș adăuga și faptul că securitatea trebuie să fie mereu prioritară în astfel de sisteme.',
            
            'Din punct de vedere tehnic, cred că abordarea corectă ar fi implementarea unui sistem hibrid care să combine...',
            
            'Sugestia ta este foarte bună! Cred că ar îmbunătăți semnificativ experiența utilizatorilor.',
            
            'Ca utilizator frecvent al platformei, pot spune că această funcționalitate ar fi extraordinar de utilă!',
            
            'Nu cred că această abordare ar fi practică din cauza limitărilor tehnice actuale. În schimb, aș sugera...',
            
            'O altă soluție la problema menționată ar putea fi...',
            
            'Sunt complet de acord! Am observat și eu aceeași problemă și cred că merită atenția dezvoltatorilor.',
            
            'Ca specialist în securitate informatică, aș recomanda implementarea unor măsuri suplimentare precum...',
            
            # IMPORTANT: Modificat pentru a menționa adrese de email în loc de username
            'Sunt de acord cu user1@example.com, dar să nu uităm și de aspectul legal al acestei probleme...'
        ]
        
        # Generăm subiecte pentru această categorie
        slug_base = category.slug
        topics_for_category = category_topics.get(slug_base, [])
        
        # Dacă nu avem titluri predefinite pentru această categorie sau nu sunt suficiente,
        # folosim titlurile generice
        while len(topics_for_category) < num_topics:
            topics_for_category.append(random.choice(generic_topics))
        
        # Limite pentru o variație naturală
        min_topics = max(3, int(num_topics * 0.7))
        actual_num_topics = random.randint(min_topics, num_topics)
        
        for i in range(actual_num_topics):
            # Alegem un titlu din lista disponibilă sau generăm unul generic
            if i < len(topics_for_category):
                title = topics_for_category[i]
            else:
                title = f"Subiect #{i+1} pentru {category.name}"
            
            # Verificăm dacă subiectul există deja
            slug = slugify(title)
            base_slug = slug
            counter = 1
            
            while Topic.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Alegem un autor aleatoriu
            author = random.choice(users)
            
            # Alegem conținut pentru postarea inițială
            content = random.choice(topic_contents)
            
            # Determinăm dacă subiectul va fi fixat (pinned) sau închis (probabilitate mică)
            is_pinned = random.random() < 0.1  # 10% șansă
            is_closed = random.random() < 0.05  # 5% șansă
            
            # Creăm subiectul
            topic = Topic.objects.create(
                title=title,
                slug=slug,
                content=content,
                category=category,
                author=author,
                is_pinned=is_pinned,
                is_closed=is_closed,
                views_count=random.randint(10, 500)  # Număr aleatoriu de vizualizări
            )
            
            # Creăm primul post (de deschidere)
            first_post = Post.objects.create(
                topic=topic,
                author=author,
                content=content
            )
            
            # Generăm reacții pentru primul post
            self.generate_reactions(first_post, users)
            
            # Generăm răspunsuri la subiect
            self.generate_replies(topic, num_posts, users, reply_contents)
    
    def generate_replies(self, topic, max_posts, users, reply_contents):
        """Generează răspunsuri pentru un subiect"""
        # Variație naturală în numărul de răspunsuri
        num_replies = random.randint(0, max_posts)
        
        for i in range(num_replies):
            # Alegem un autor aleatoriu diferit de autorul subiectului (de obicei)
            if random.random() < 0.8:  # 80% șansă ca autorul să fie diferit
                potential_authors = [u for u in users if u != topic.author]
                if potential_authors:
                    author = random.choice(potential_authors)
                else:
                    author = random.choice(users)
            else:
                author = random.choice(users)
            
            # Alegem conținut pentru răspuns
            content = random.choice(reply_contents)
            
            # Eventual adăugăm o mențiune către autorul subiectului
            if random.random() < 0.3:  # 30% șansă
                # IMPORTANT: Utilizăm email în loc de username pentru mențiuni
                content = f"@{topic.author.email} {content}"
            
            # Decidem dacă acest răspuns va fi marcat ca soluție (doar pentru primul sau al doilea răspuns)
            is_solution = False
            if i <= 1 and random.random() < 0.2:  # 20% șansă pentru primele două răspunsuri
                is_solution = True
                # Dacă marcăm acest răspuns ca soluție, ne asigurăm că nu există altă soluție
                Post.objects.filter(topic=topic, is_solution=True).update(is_solution=False)
            
            # Creăm postarea
            post = Post.objects.create(
                topic=topic,
                author=author,
                content=content,
                is_solution=is_solution
            )
            
            # Generăm reacții pentru acest post
            self.generate_reactions(post, users)
    
    def generate_reactions(self, post, users):
        """Generează reacții pentru o postare"""
        # Decidem câți utilizatori vor reacționa (între 0 și 5)
        num_reactors = random.randint(0, min(5, len(users)))
        
        # Alegem utilizatori aleatori diferiți pentru a reacționa
        reactors = random.sample(users, num_reactors)
        
        for user in reactors:
            # Nu permitem autorului să reacționeze la propria postare
            if user == post.author:
                continue
                
            # Alegem un tip de reacție
            reaction_type = random.choice(['like', 'helpful', 'insightful'])
            
            # Creăm reacția
            Reaction.objects.create(
                post=post,
                user=user,
                reaction_type=reaction_type
            )