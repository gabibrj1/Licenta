from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from news.models import NewsArticle, Category
from django.utils import timezone
from django.db import transaction
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Populează tabelul de articole de știri cu date inițiale'

    def handle(self, *args, **options):
        self.stdout.write('Începe popularea articolelor de știri...')
        
        # Verifică existența unui utilizator admin
        try:
            # Încercăm să obținem un admin folosind email în loc de username
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if not admin_user:
                # Dacă nu există un admin, creăm unul
                admin_user = User.objects.create_superuser(
                    email='admin@example.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User'
                )
                self.stdout.write(self.style.SUCCESS('Utilizatorul admin a fost creat.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Utilizator admin găsit: {admin_user.email}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Eroare la obținerea/crearea utilizatorului admin: {str(e)}'))
            return
        
        # Verifică existența categoriilor
        if not Category.objects.exists():
            self.stdout.write(self.style.ERROR('Nu există categorii. Rulează mai întâi comanda populate_categories.'))
            return
        
        categories = {}
        for category in Category.objects.all():
            categories[category.slug] = category
        
        # Articolele care vor fi create
        articles_data = [
            {
                'title': 'Lansarea sistemului SmartVote în România',
                'slug': 'lansarea-sistemului-smartvote-in-romania',
                'content': 'Astăzi a fost lansat oficial sistemul SmartVote în România, un sistem inovator care își propune să transforme modul în care cetățenii participă la procesul electoral.',
                'summary': 'Sistemul SmartVote a fost lansat oficial în România cu scopul de a facilita participarea cetățenilor la procesul electoral.',
                'image': 'news/images/smartvote_launch.jpg',
                'publish_date': timezone.now(),
                'author': admin_user,
                'category': categories.get('elections'),
                'article_type': 'news',
                'is_featured': True,
                'views_count': 120
            },
            {
                'title': 'Analiză: Impactul votului electronic asupra prezenței la urne',
                'slug': 'analiza-impactul-votului-electronic-asupra-prezentei-la-urne',
                'content': 'Studii recente arată că implementarea sistemelor de vot electronic poate crește prezența la urne cu până la 15% în rândul tinerilor.',
                'summary': 'Studii recente arată că votul electronic crește prezența la urne în rândul tinerilor.',
                'image': 'news/images/e_voting_turnout.jpg',
                'publish_date': timezone.now() - datetime.timedelta(days=2),
                'author': admin_user,
                'category': categories.get('elections'),
                'article_type': 'analysis',
                'is_featured': True,
                'views_count': 85
            },
            {
                'title': 'Securitatea votului electronic: mituri și realități',
                'slug': 'securitatea-votului-electronic-mituri-si-realitati',
                'content': 'Experții în securitate informatică dezbat miturile comune despre vulnerabilitățile sistemelor de vot electronic.',
                'summary': 'Experții în securitate dezbat miturile despre vulnerabilitățile sistemelor de vot electronic.',
                'image': 'news/images/e_voting_security.jpg',
                'publish_date': timezone.now() - datetime.timedelta(days=4),
                'author': admin_user,
                'category': categories.get('security'),
                'article_type': 'analysis',
                'is_featured': False,
                'views_count': 92
            },
            {
                'title': 'Dezbatere parlamentară pe tema votului electronic',
                'slug': 'dezbatere-parlamentara-pe-tema-votului-electronic',
                'content': 'Parlamentul României a organizat o dezbatere pe tema implementării votului electronic pentru următoarele alegeri.',
                'summary': 'Parlamentul a organizat o dezbatere despre implementarea votului electronic pentru viitoarele alegeri.',
                'image': 'news/images/parliament_debate.jpg',
                'publish_date': timezone.now() - datetime.timedelta(days=1),
                'author': admin_user,
                'category': categories.get('politics'),
                'article_type': 'news',
                'is_featured': True,
                'views_count': 75
            },
            {
                'title': 'Tehnologii blockchain în procesele electorale',
                'slug': 'tehnologii-blockchain-in-procesele-electorale',
                'content': 'Cum poate tehnologia blockchain să asigure securitatea și transparența în sistemele de vot electronic moderne.',
                'summary': 'Explorăm potențialul tehnologiei blockchain pentru securizarea sistemelor de vot electronic.',
                'image': 'news/images/blockchain_voting.jpg',
                'publish_date': timezone.now() - datetime.timedelta(days=3),
                'author': admin_user,
                'category': categories.get('technology'),
                'article_type': 'analysis',
                'is_featured': True,
                'views_count': 110
            },
            {
                'title': 'Estonia: 15 ani de vot electronic - lecții învățate',
                'slug': 'estonia-15-ani-de-vot-electronic-lectii-invatate',
                'content': 'Estonia, pionier în implementarea votului electronic, oferă lecții valoroase pentru țările care doresc să adopte această tehnologie.',
                'summary': 'Lecții valoroase din experiența Estoniei cu votul electronic în ultimii 15 ani.',
                'image': 'news/images/estonia_e_voting.jpg',
                'publish_date': timezone.now() - datetime.timedelta(days=5),
                'author': admin_user,
                'category': categories.get('elections'),
                'article_type': 'news',
                'is_featured': False,
                'views_count': 65
            },
            {
                'title': 'Măsuri de securitate pentru protejarea votului electronic',
                'slug': 'masuri-de-securitate-pentru-protejarea-votului-electronic',
                'content': 'Experții în securitate cibernetică recomandă implementarea mai multor niveluri de protecție pentru sistemele de vot electronic.',
                'summary': 'Recomandări pentru implementarea mai multor niveluri de protecție în sistemele de vot electronic.',
                'image': 'news/images/security_measures.jpg',
                'publish_date': timezone.now() - datetime.timedelta(days=6),
                'author': admin_user,
                'category': categories.get('security'),
                'article_type': 'news',
                'is_featured': False,
                'views_count': 48
            },
            {
                'title': 'Tendințe internaționale în adoptarea votului electronic',
                'slug': 'tendinte-internationale-in-adoptarea-votului-electronic',
                'content': 'Tot mai multe țări consideră implementarea sistemelor de vot electronic pentru a facilita accesul cetățenilor la procesul electoral.',
                'summary': 'Analiză a tendințelor globale în adoptarea sistemelor de vot electronic.',
                'image': 'news/images/global_trends.jpg',
                'publish_date': timezone.now() - datetime.timedelta(days=7),
                'author': admin_user,
                'category': categories.get('elections'),
                'article_type': 'analysis',
                'is_featured': True,
                'views_count': 88
            },
            {
                'title': 'Perspective legislative privind votul electronic în România',
                'slug': 'perspective-legislative-privind-votul-electronic-in-romania',
                'content': 'Analiză a cadrului legislativ actual și a schimbărilor necesare pentru implementarea votului electronic în România.',
                'summary': 'Analiză a modificărilor legislative necesare pentru implementarea votului electronic în România.',
                'image': 'news/images/legislative_perspective.jpg',
                'publish_date': timezone.now() - datetime.timedelta(days=8),
                'author': admin_user,
                'category': categories.get('politics'),
                'article_type': 'analysis',
                'is_featured': False,
                'views_count': 72
            },
            {
                'title': 'Conferință internațională despre viitorul sistemelor de vot',
                'slug': 'conferinta-internationala-despre-viitorul-sistemelor-de-vot',
                'content': 'Experți din întreaga lume s-au întâlnit la București pentru a discuta despre viitorul sistemelor de vot și rolul tehnologiei.',
                'summary': 'Experți internaționali dezbat viitorul sistemelor de vot la o conferință în București.',
                'image': 'news/images/international_conference.jpg',
                'publish_date': timezone.now() - datetime.timedelta(days=10),
                'author': admin_user,
                'category': categories.get('elections'),
                'article_type': 'news',
                'is_featured': True,
                'views_count': 95
            }
        ]
        
        # Folosim transaction pentru a asigura integritatea datelor
        with transaction.atomic():
            for article_data in articles_data:
                # Verifică dacă categoria există
                if article_data['category'] is None:
                    self.stdout.write(self.style.WARNING(f"Categoria pentru articolul '{article_data['title']}' nu există. Articolul nu va fi creat."))
                    continue
                
                try:
                    article, created = NewsArticle.objects.get_or_create(
                        slug=article_data['slug'],
                        defaults=article_data
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Articolul '{article.title}' a fost creat."))
                    else:
                        self.stdout.write(self.style.WARNING(f"Articolul '{article.title}' există deja."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Eroare la crearea articolului '{article_data['title']}': {e}"))
        
        self.stdout.write(self.style.SUCCESS('Popularea articolelor de știri a fost finalizată cu succes!'))