from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import requests
import json
from datetime import datetime, timedelta
from .models import NewsArticle, Category, ExternalNewsSource, ElectionAnalyticsChart, ChartDataset, ChartDataPoint
from .serializers import NewsArticleSerializer, CategorySerializer, NewsArticleDetailSerializer
import logging


logger = logging.getLogger(__name__)

def news_home(request):
    """
    View pentru pagina principală de știri
    """
    featured_articles = NewsArticle.objects.filter(is_featured=True, is_published=True)[:6]
    latest_news = NewsArticle.objects.filter(is_published=True, article_type='news')[:8]
    latest_analysis = NewsArticle.objects.filter(is_published=True, article_type='analysis')[:5]
    categories = Category.objects.all()
    
    context = {
        'featured_articles': featured_articles,
        'latest_news': latest_news,
        'latest_analysis': latest_analysis,
        'categories': categories,
    }
    
    return render(request, 'news/home.html', context)

def article_detail(request, slug):
    """
    View pentru detaliile unui articol
    """
    article = get_object_or_404(NewsArticle, slug=slug, is_published=True)
    
    # Increment views count
    article.views_count += 1
    article.save()
    
    # Get related articles
    related_articles = NewsArticle.objects.filter(
        category=article.category, 
        is_published=True
    ).exclude(id=article.id)[:3]
    
    context = {
        'article': article,
        'related_articles': related_articles,
    }
    
    return render(request, 'news/article_detail.html', context)

def category_articles(request, slug):
    """
    View pentru articole dintr-o categorie
    """
    category = get_object_or_404(Category, slug=slug)
    articles = NewsArticle.objects.filter(category=category, is_published=True)
    
    context = {
        'category': category,
        'articles': articles,
    }
    
    return render(request, 'news/category_articles.html', context)

class LatestNewsAPI(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        API endpoint pentru cele mai recente știri
        """
        try:
            category_slug = request.query_params.get('category', None)
            article_type = request.query_params.get('type', None)
            limit = int(request.query_params.get('limit', 10))
            
            articles = NewsArticle.objects.filter(is_published=True)
            
            if category_slug and category_slug != 'all':
                try:
                    category = Category.objects.get(slug=category_slug)
                    articles = articles.filter(category=category)
                except Category.DoesNotExist:
                    # Dacă categoria nu există, returnăm o listă goală
                    logger.warning(f"Categoria cu slug-ul '{category_slug}' nu există")
                    return Response([], status=status.HTTP_200_OK)
            
            if article_type and article_type != 'all':
                articles = articles.filter(article_type=article_type)
            
            articles = articles.order_by('-publish_date')[:limit]
            
            serializer = NewsArticleSerializer(articles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Eroare la obținerea știrilor: {str(e)}")
            # În loc să returnăm eroare, returnăm o listă goală
            return Response([], status=status.HTTP_200_OK)

class ExternalNewsAPI(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        API endpoint pentru știri externe
        """
        try:
            # Verifică dacă există surse externe de știri în baza de date
            sources = ExternalNewsSource.objects.filter(is_active=True)
            
            if sources.exists():
                # În implementarea reală, aici s-ar face apeluri către API-urile externe
                # Pentru simplitate, vom returna știri mock similare cu sursele din baza de date
                return Response(
                    self.get_mock_news_from_sources(sources),
                    status=status.HTTP_200_OK
                )
            else:
                # Dacă nu există surse, folosim datele mock implicite
                return Response(
                    self.get_mock_news(),
                    status=status.HTTP_200_OK
                )
        
        except Exception as e:
            logger.error(f"Eroare la obținerea știrilor externe: {str(e)}")
            return Response(
                self.get_mock_news(),
                status=status.HTTP_200_OK
            )
    
    def get_mock_news_from_sources(self, sources):
        """
        Generează știri mock bazate pe sursele din baza de date
        """
        news = []
        
        # Definim datele pentru știrile unice
        news_data = [
            {
                'title': 'Analiză: Impactul votului electronic în contextul actual al României',
                'description': 'O evaluare detaliată a modului în care votul electronic poate transforma procesul democratic în era digitală în România.',
                'url': 'https://democracycenter.ro/publicatii/cat-de-oportuna-este-introducerea-votului-prin-internet-romania/',
                'urlToImage': '/static/images/news/default1.jpg',
                'source': {'name': 'Centrul pentru studiul democratiei'},
                'author': 'Echipa de analiză'
            },
            {
                'title': 'Securitate și transparență: Provocările implementării votului electronic în România',
                'description': 'Experții dezbat echilibrul optim între securitate și accesibilitate în sistemele moderne de vot electronic pentru alegerile românești.',
                'url': 'https://www.code4.ro/ro/blog/securitatea-sistemelor-de-vot-electronic',
                'urlToImage': '/static/images/news/default2.jpg',
                'source': {'name': 'Code for Romania'},
                'author': 'Echipa de cercetare'
            },
            {
                'title': 'Știri politice de ultimă oră',
                'description': 'Ultimele informații din sfera politică românească și impactul asupra sistemelor de vot.',
                'url': 'https://www.digi24.ro/stiri/actualitate/politica',
                'urlToImage': '/static/images/news/default3.jpg',
                'source': {'name': 'DIGI 24'},
                'author': 'Redacția Digi24'
            },
            {
                'title': 'Actualizări legislative și reglementări',
                'description': 'Cele mai recente modificări legislative care afectează implementarea sistemelor de vot electronic în România.',
                'url': 'https://sgg.gov.ro/1/wp-content/uploads/2023/01/INFORMARE.pdf',
                'urlToImage': '/static/images/news/default4.jpg',
                'source': {'name': 'Guvernul României'},
                'author': 'Secretariatul General al Guvernului'
            },
            {
                'title': 'Votul electronic: avantaje și riscuri de securitate',
                'description': 'O analiză comprehensivă a beneficiilor și vulnerabilităților potențiale ale implementării votului electronic în România.',
                'url': 'https://pressone.ro/votul-electronic-avantaje-si-riscuri-de-securitate',
                'urlToImage': '/static/images/news/default5.jpg',
                'source': {'name': 'PressOne'},
                'author': 'Echipa editorială'
            }
        ]
        
        # Adăugăm datele de publicare (timestamp actual pentru prima știre, 
        # apoi decrementăm cu câte o zi pentru fiecare știre următoare)
        for i, news_item in enumerate(news_data):
            news_item['publishedAt'] = (datetime.now() - timedelta(days=i)).isoformat()
            news.append(news_item)
        
        return news
    
    def get_mock_news(self):
        """
        Returnează știri mock pentru dezvoltare cu link-uri către site-uri românești
        """
        return [
            {
                'title': 'Analiză: Impactul votului electronic în contextul actual al României',
                'description': 'O evaluare detaliată a modului în care votul electronic poate transforma procesul democratic în era digitală în România.',
                'url': 'https://democracycenter.ro/publicatii/cat-de-oportuna-este-introducerea-votului-prin-internet-romania/',
                'urlToImage': '/static/images/news/default1.jpg',
                'publishedAt': datetime.now().isoformat(),
                'source': {'name': 'Centrul pentru studiul democratiei'},
                'author': 'Echipa de analiză'
            },
            {
                'title': 'Securitate și transparență: Provocările implementării votului electronic în România',
                'description': 'Experții dezbat echilibrul optim între securitate și accesibilitate în sistemele moderne de vot electronic pentru alegerile românești.',
                'url': 'https://www.code4.ro/ro/blog/securitatea-sistemelor-de-vot-electronic',
                'urlToImage': '/static/images/news/default2.jpg',
                'publishedAt': (datetime.now() - timedelta(days=1)).isoformat(),
                'source': {'name': 'Code for Romania'},
                'author': 'Echipa de cercetare'
            },
            {
                'title': 'Știri politice de ultimă oră',
                'description': 'Ultimele informații din sfera politică românească și impactul asupra sistemelor de vot.',
                'url': 'https://www.digi24.ro/stiri/actualitate/politica',
                'urlToImage': '/static/images/news/default3.jpg',
                'publishedAt': (datetime.now() - timedelta(days=2)).isoformat(),
                'source': {'name': 'DIGI 24'},
                'author': 'Redacția Digi24'
            },
            {
                'title': 'Actualizări legislative și reglementări',
                'description': 'Cele mai recente modificări legislative care afectează implementarea sistemelor de vot electronic în România.',
                'url': 'https://sgg.gov.ro/1/wp-content/uploads/2023/01/INFORMARE.pdf',
                'urlToImage': '/static/images/news/default4.jpg',
                'publishedAt': (datetime.now() - timedelta(days=3)).isoformat(),
                'source': {'name': 'Guvernul României'},
                'author': 'Secretariatul General al Guvernului'
            },
            {
                'title': 'Votul electronic: avantaje și riscuri de securitate',
                'description': 'O analiză comprehensivă a beneficiilor și vulnerabilităților potențiale ale implementării votului electronic în România.',
                'url': 'https://pressone.ro/votul-electronic-avantaje-si-riscuri-de-securitate',
                'urlToImage': '/static/images/news/default5.jpg',
                'publishedAt': (datetime.now() - timedelta(days=4)).isoformat(),
                'source': {'name': 'PressOne'},
                'author': 'Echipa editorială'
            }
        ]

class ElectionAnalyticsAPI(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        API endpoint pentru date analitice despre alegeri
        """
        try:
            # În loc să returnăm date hardcodate, preluăm din baza de date
            charts = ElectionAnalyticsChart.objects.filter(is_active=True)
            data = [chart.to_dict() for chart in charts]
            
            return Response(
                data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Eroare la obținerea datelor analitice: {str(e)}")
            return Response(
                {'error': 'Eroare la obținerea datelor analitice'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_mock_analytics(self):
        """
        Returnează date mock pentru grafice și analize
        """
        return [
            {
                'id': 1,
                'title': 'Prezența la vot în ultimele alegeri',
                'type': 'line',
                'data': {
                    'labels': ['2000', '2004', '2008', '2012', '2016', '2020'],
                    'datasets': [
                        {
                            'label': 'Prezență la vot (%)',
                            'data': [65, 57, 58, 64, 39, 52],
                            'borderColor': '#2e86de',
                            'fill': False
                        }
                    ]
                }
            },
            {
                'id': 2,
                'title': 'Distribuția voturilor pe grupe de vârstă',
                'type': 'bar',
                'data': {
                    'labels': ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
                    'datasets': [
                        {
                            'label': 'Participare (%)',
                            'data': [32, 48, 56, 67, 72, 68],
                            'backgroundColor': [
                                '#54a0ff', '#2e86de', '#0c75c7',
                                '#065a9d', '#044680', '#02386a'
                            ]
                        }
                    ]
                }
            },
            {
                'id': 3,
                'title': 'Metode de vot utilizate',
                'type': 'pie',
                'data': {
                    'labels': ['La secție', 'Prin corespondență', 'Electronic', 'Mobil'],
                    'datasets': [
                        {
                            'data': [75, 10, 12, 3],
                            'backgroundColor': ['#ff6b6b', '#5f27cd', '#1dd1a1', '#feca57']
                        }
                    ]
                }
            }
        ]
    
class ArticleDetailAPI(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        """
        API endpoint pentru obținerea detaliilor unui articol specific
        """
        try:
            article = get_object_or_404(NewsArticle, slug=slug, is_published=True)
            
            # Incrementează numărul de vizualizări
            article.views_count += 1
            article.save()
            
            # Serializează articolul cu toate detaliile, inclusiv conținut complet
            serializer = NewsArticleDetailSerializer(article)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Eroare la obținerea detaliilor articolului: {str(e)}")
            return Response(
                {'error': 'Articolul nu a putut fi găsit sau afișat.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
def get_default_image_path(category_slug=None):
    """Returnează calea către o imagine implicită bazată pe categorie"""
    
    default_images = {
        'elections': 'news/images/defaults/elections.jpg',
        'politics': 'news/images/defaults/politics.jpg',
        'technology': 'news/images/defaults/technology.jpg',
        'security': 'news/images/defaults/security.jpg',
        'general': 'news/images/defaults/default.jpg',
    }
    
    return default_images.get(category_slug, default_images['general'])

class OpinionsAPI(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        API endpoint pentru opinii
        """
        try:
            limit = int(request.query_params.get('limit', 5))
            
            # Obținem articolele de tip opinie
            opinions = NewsArticle.objects.filter(
                is_published=True, 
                article_type='opinion'
            ).order_by('-publish_date')[:limit]
            
            serializer = NewsArticleSerializer(opinions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Eroare la obținerea opiniilor: {str(e)}")
            return Response([], status=status.HTTP_200_OK)