from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from news.models import NewsArticle, Category
from django.utils import timezone
from django.db import transaction
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Populează tabelul de articole de tip opinie'

    def handle(self, *args, **options):
        self.stdout.write('Începe popularea opiniilor...')
        
        # Verifică existența unui utilizator admin
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if not admin_user:
                self.stdout.write(self.style.ERROR('Nu există un admin. Rulează mai întâi comanda populate_news_articles.'))
                return
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Eroare la obținerea utilizatorului admin: {str(e)}'))
            return
        
        # Verifică existența categoriilor
        if not Category.objects.exists():
            self.stdout.write(self.style.ERROR('Nu există categorii. Rulează mai întâi comanda populate_categories.'))
            return
        
        categories = {}
        for category in Category.objects.all():
            categories[category.slug] = category
        
        # Opiniile care vor fi create
        opinions_data = [
            {
                'title': 'De ce votul electronic este viitorul democrației în România',
                'slug': 'de-ce-votul-electronic-este-viitorul-democratiei-in-romania',
                'content': 'În contextul actual, România are nevoie mai mult ca niciodată de soluții inovatoare pentru a crește participarea cetățenilor la procesul electoral. Votul electronic reprezintă nu doar o modernizare tehnologică, ci și o modalitate de a readuce tinerii în procesul democratic.\n\nStatisticile arată că prezența la vot în rândul tinerilor cu vârste între 18-35 de ani este semnificativ mai scăzută decât în alte categorii de vârstă. Implementarea unui sistem de vot electronic ar elimina multe dintre barierele care descurajează participarea la vot: timpul pierdut la cozi, distanța până la secția de votare sau imposibilitatea de a vota din cauza programului de lucru.\n\nExperiența altor țări europene, în special Estonia, a demonstrat că votul electronic poate crește semnificativ rata de participare la vot. Estonia, care a implementat votul electronic încă din 2005, a înregistrat o creștere constantă a utilizării acestui sistem, ajungând ca aproape 50% din voturi să fie exprimate online la ultimele alegeri.\n\nDesigur, există provocări legate de securitate, dar tehnologiile moderne de criptare, autentificare în mai multe etape și blockchain oferă soluții viabile. Investiția în educația digitală a populației și în infrastructura necesară ar fi, de asemenea, esențiale.\n\nRomânia are șansa de a face un salt important în modernizarea sistemului său electoral, aliniindu-se la tendințele digitale globale și oferind cetățenilor săi un proces electoral mai accesibil și mai eficient. Este timpul să privim spre viitor și să îmbrățișăm tehnologiile care pot întări democrația.',
                'summary': 'Votul electronic reprezintă o oportunitate unică de a revitaliza democrația în România și de a crește participarea electorală în rândul tinerilor.',
                'publish_date': timezone.now() - datetime.timedelta(days=3),
                'author': admin_user,
                'category': categories.get('elections'),
                'article_type': 'opinion',
                'is_featured': False,
                'views_count': 45
            },
            {
                'title': 'Provocările implementării votului electronic necesită o abordare graduală',
                'slug': 'provocarile-implementarii-votului-electronic-necesita-o-abordare-graduala',
                'content': 'Deși sunt un susținător al modernizării procesului electoral, cred că implementarea votului electronic în România trebuie să urmeze un proces gradual și bine planificat. Experiențele altor țări au demonstrat că graba poate duce la probleme semnificative de securitate și încredere.\n\nÎn primul rând, România se confruntă cu disparități majore în ceea ce privește accesul la tehnologie și competențele digitale. Conform statisticilor recente, aproximativ 30% din populația României nu are acces regulat la internet, iar în zonele rurale situația este și mai gravă. Implementarea votului electronic fără rezolvarea acestor disparități ar putea crea un nou tip de inegalitate în procesul electoral.\n\nÎn al doilea rând, încrederea publicului în securitatea votului electronic este esențială. Un sondaj recent arată că doar 45% dintre români ar avea încredere să voteze electronic, restul exprimându-și îngrijorări legate de posibile fraude sau manipulări. Construirea acestei încrederi necesită timp, educație și transparență totală în dezvoltarea sistemului.\n\nO abordare graduală ar putea începe cu implementarea votului electronic în paralel cu metodele tradiționale, poate inițial doar pentru românii din diaspora. Apoi, pe baza rezultatelor și lecțiilor învățate, sistemul ar putea fi extins treptat la nivel național.\n\nExperiența Norvegiei, care a testat votul electronic dar a decis să nu continue din cauza îngrijorărilor legate de securitate, ar trebui să ne servească drept avertisment. Este mai bine să avansăm cu pași mici dar siguri, decât să implementăm în grabă un sistem problematic care ar putea submina încrederea în procesul electoral.\n\nÎn concluzie, deși votul electronic reprezintă viitorul, drumul către acest viitor trebuie parcurs cu prudență și planificare atentă.',
                'summary': 'Implementarea votului electronic în România trebuie să fie un proces gradual, bazat pe testare extinsă și educarea populației.',
                'publish_date': timezone.now() - datetime.timedelta(days=5),
                'author': admin_user,
                'category': categories.get('technology'),
                'article_type': 'opinion',
                'is_featured': False,
                'views_count': 38
            },
            {
                'title': 'Votul electronic ar putea rezolva problema diasporei românești',
                'slug': 'votul-electronic-ar-putea-rezolva-problema-diasporei-romanesti',
                'content': 'Pentru cei peste 4 milioane de români din diaspora, votul reprezintă adesea o provocare logistică majoră. Cozile interminabile la secțiile de votare din străinătate sunt o imagine care a făcut înconjurul lumii la fiecare ciclu electoral. Votul electronic ar putea fi soluția pe care diaspora o așteaptă de ani de zile.\n\nPentru românii care locuiesc în străinătate, exercitarea dreptului de vot implică adesea călătorii de sute de kilometri până la cea mai apropiată secție de votare, stat la cozi timp de ore întregi și, în unele cazuri, imposibilitatea de a vota din cauza închiderii urnelor înainte ca toți cetățenii să-și fi exprimat votul. Această situație este nu doar frustrantă, ci și profund injustă, privând efectiv milioane de cetățeni români de dreptul lor fundamental de a participa la procesul democratic.\n\nVotul electronic ar elimina toate aceste bariere. Un român din Dublin, Paris sau Toronto ar putea vota confortabil de acasă, fără să-și ia o zi liberă de la muncă, fără să călătorească și fără stresul cozilor interminabile.\n\nÎn plus, participarea diasporei la vot ar crește semnificativ, oferind o reprezentare mai echitabilă a opiniilor și intereselor acestei comunități importante. La ultimele alegeri prezidențiale, deși prezența la vot în diaspora a fost record, ea reprezintă doar o fracțiune din potențialul electoral al românilor din străinătate.\n\nDesigur, implementarea unui sistem de vot electronic pentru diaspora ar veni cu propriile provocări, inclusiv verificarea identității votanților și asigurarea securității procesului. Dar aceste provocări pot fi depășite prin utilizarea tehnologiilor moderne de autentificare și criptare.\n\nEste timpul ca România să ofere diasporei sale respectul pe care îl merită, implementând un sistem de vot care să le permită tuturor românilor, indiferent unde se află, să-și exercite dreptul democratic cu demnitate și eficiență.',
                'summary': 'Românii din diaspora ar beneficia cel mai mult de implementarea votului electronic, eliminând cozile și problemele logistice.',
                'publish_date': timezone.now() - datetime.timedelta(days=7),
                'author': admin_user,
                'category': categories.get('politics'),
                'article_type': 'opinion',
                'is_featured': False,
                'views_count': 72
            },
            {
                'title': 'Securitatea cibernetică trebuie să fie prioritatea numărul unu',
                'slug': 'securitatea-cibernetica-trebuie-sa-fie-prioritatea-numarul-unu',
                'content': 'În discuțiile despre votul electronic, aspectul securității este adesea menționat, dar rareori aprofundat. Ca expert în securitate informatică, pot spune că provocările sunt reale și multiple. De la atacuri DDoS la tentative de fraudă, un sistem de vot electronic trebuie să facă față unor amenințări sofisticate și în continuă evoluție.\n\nÎn primul rând, orice sistem de vot electronic trebuie proiectat cu principiul "securitate prin design". Aceasta înseamnă că securitatea nu este un element adăugat ulterior, ci o componentă fundamentală a arhitecturii sistemului. Criptarea end-to-end, autentificarea multi-factor și tehnologiile blockchain sunt esențiale, dar nu suficiente.\n\nÎn al doilea rând, transparența codului sursă este crucială. Un sistem de vot electronic destinat democrației trebuie să fie el însuși democratic - deschis pentru examinare și verificare independentă. Codul sursă închis ar genera suspiciuni justificate și ar submina încrederea în sistem.\n\nÎn al treilea rând, auditul post-electoral trebuie să fie riguros și complet transparent. Trebuie să existe metode de verificare a faptului că voturile au fost înregistrate corect, fără a compromite anonimitatea votanților.\n\nÎn al patrulea rând, implementarea unui sistem de vot electronic necesită o strategie robustă de gestionare a incidentelor. Atacurile cibernetice sunt inevitabile, iar capacitatea de a detecta, răspunde și recupera rapid este esențială.\n\nÎn contextul României, unde infrastructura digitală este încă în dezvoltare și unde atacurile cibernetice au vizat în trecut instituții publice, aceste considerente de securitate sunt și mai importante.\n\nSunt un susținător al votului electronic, dar numai dacă acesta este implementat cu cele mai înalte standarde de securitate. Un sistem vulnerabil ar fi mai rău decât lipsa unui sistem electronic, subminând încrederea în procesul democratic și deschizând ușa pentru interferențe nedorite.',
                'summary': 'Implementarea votului electronic trebuie să aibă securitatea cibernetică ca prioritate absolută pentru a asigura integritatea procesului electoral.',
                'publish_date': timezone.now() - datetime.timedelta(days=10),
                'author': admin_user,
                'category': categories.get('security'),
                'article_type': 'opinion',
                'is_featured': False,
                'views_count': 56
            },
            {
                'title': 'Educația digitală - condiție esențială pentru succesul votului electronic',
                'slug': 'educatia-digitala-conditie-esentiala-pentru-succesul-votului-electronic',
                'content': 'Introducerea votului electronic nu poate avea succes fără o campanie amplă de educare a populației. Competențele digitale variază semnificativ în funcție de vârstă, mediu de reședință și nivel de educație. Pentru ca votul electronic să nu devină un factor de excluziune, este nevoie de programe educaționale adaptate diverselor categorii de alegători.\n\nConform unui studiu recent, aproximativ 40% din populația României are competențe digitale scăzute sau inexistente. Această realitate reprezintă o provocare majoră pentru implementarea votului electronic. Fără intervenții educaționale specifice, riscăm să creăm un sistem care, deși teoretic mai accesibil, în practică exclude o parte semnificativă a populației.\n\nEducația digitală necesară pentru votul electronic ar trebui să aibă două componente principale. Prima ar fi educația tehnică - cum se utilizează concret platforma de vot, cum se autentifică utilizatorul, cum se navighează prin interfață, etc. A doua componentă, la fel de importantă, ar fi educația civică digitală - înțelegerea importanței securității parolelor, recunoașterea tentativelor de phishing, înțelegerea modului în care funcționează sistemul în ansamblu.\n\nO soluție practică ar fi crearea unor centre de instruire în fiecare comunitate, unde cetățenii să poată participa la simulări de vot electronic și să primească asistență personalizată. De asemenea, ar fi utilă dezvoltarea unei aplicații de simulare care să permită utilizatorilor să se familiarizeze cu procesul înainte de alegerile reale.\n\nȘcolile ar putea juca un rol crucial, nu doar în educarea elevilor, ci și ca centre comunitare pentru educarea adulților. Profesorii, în special cei de informatică și educație civică, ar putea fi formați pentru a deveni la rândul lor formatori pentru comunitate.\n\nInvestiția în educația digitală nu ar aduce beneficii doar pentru implementarea votului electronic, ci ar avea un impact pozitiv asupra întregii societăți, contribuind la reducerea decalajului digital și la creșterea competitivității economice a României.',
                'summary': 'Fără o creștere a nivelului de educație digitală în rândul populației, votul electronic riscă să devină un factor de excluziune.',
                'publish_date': timezone.now() - datetime.timedelta(days=12),
                'author': admin_user,
                'category': categories.get('technology'),
                'article_type': 'opinion',
                'is_featured': False,
                'views_count': 49
            }
        ]
        
        # Folosim transaction pentru a asigura integritatea datelor
        with transaction.atomic():
            for opinion_data in opinions_data:
                # Verifică dacă categoria există
                if opinion_data['category'] is None:
                    self.stdout.write(self.style.WARNING(f"Categoria pentru opinia '{opinion_data['title']}' nu există. Opinia nu va fi creată."))
                    continue
                
                try:
                    opinion, created = NewsArticle.objects.get_or_create(
                        slug=opinion_data['slug'],
                        defaults=opinion_data
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Opinia '{opinion.title}' a fost creată."))
                    else:
                        self.stdout.write(self.style.WARNING(f"Opinia '{opinion.title}' există deja."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Eroare la crearea opiniei '{opinion_data['title']}': {e}"))
        
        self.stdout.write(self.style.SUCCESS('Popularea opiniilor a fost finalizată cu succes!'))