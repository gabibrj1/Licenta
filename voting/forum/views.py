from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, F
from django.utils import timezone
from rest_framework import status, viewsets, generics, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail

from .models import Category, Topic, Post, Reaction, Attachment, Notification, NewsletterSubscription, NotificationPreferences
from .serializers import (
    CategorySerializer, TopicListSerializer, TopicDetailSerializer, 
    TopicCreateUpdateSerializer, PostListSerializer, PostDetailSerializer,
    PostCreateUpdateSerializer, ReactionSerializer, AttachmentSerializer,
    NotificationSerializer, NotificationPreferencesSerializer
)

import logging
logger = logging.getLogger(__name__)

class ForumPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):

    # API endpoint pentru vizualizarea categoriilor
    queryset = Category.objects.filter(is_active=True).order_by('order', 'name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """Obține subiectele dintr-o categorie specifică"""
        category = self.get_object()
        topics = Topic.objects.filter(category=category, is_approved=True).order_by('-is_pinned', '-last_activity')
        
        paginator = ForumPagination()
        paginated_topics = paginator.paginate_queryset(topics, request)
        
        serializer = TopicListSerializer(paginated_topics, many=True)
        return paginator.get_paginated_response(serializer.data)

class TopicViewSet(viewsets.ModelViewSet):
    
    # API endpoint pentru gestionarea subiectelor
 
    queryset = Topic.objects.filter(is_approved=True)
    permission_classes = [IsAuthenticated]
    pagination_class = ForumPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TopicListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TopicCreateUpdateSerializer
        return TopicDetailSerializer
    
    def get_queryset(self):
        queryset = Topic.objects.filter(is_approved=True)
        
        # Filtrare după categorie
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filtrare după autor
        author_id = self.request.query_params.get('author', None)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Filtrare după cuvinte cheie în titlu sau conținut
        search_term = self.request.query_params.get('search', None)
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) | 
                Q(content__icontains=search_term)
            )
        
        # Sortare după diferite criterii
        sort_by = self.request.query_params.get('sort', None)
        if sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'activity':
            queryset = queryset.order_by('-last_activity')
        elif sort_by == 'views':
            queryset = queryset.order_by('-views_count')
        elif sort_by == 'responses':
            queryset = queryset.annotate(post_count=Count('posts')).order_by('-post_count')
        else:
            # Sortare default
            queryset = queryset.order_by('-is_pinned', '-last_activity')
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Incrementare contor de vizualizări
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Returnează cele mai recente subiecte"""
        topics = Topic.objects.filter(is_approved=True).order_by('-last_activity')[:10]
        serializer = TopicListSerializer(topics, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Returnează cele mai populare subiecte (cu cele mai multe vizualizări)"""
        topics = Topic.objects.filter(is_approved=True).order_by('-views_count')[:10]
        serializer = TopicListSerializer(topics, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Închide un subiect - doar autorul sau adminii pot face asta"""
        topic = self.get_object()
        
        # Verifică permisiunile
        if not (request.user == topic.author or request.user.is_staff):
            return Response(
                {'error': 'Nu aveți permisiunea de a închide acest subiect.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        topic.is_closed = True
        topic.save(update_fields=['is_closed'])
        
        return Response({'message': 'Subiect închis cu succes.'})
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Redeschide un subiect închis"""
        topic = self.get_object()
        
        # Verifică permisiunile
        if not (request.user == topic.author or request.user.is_staff):
            return Response(
                {'error': 'Nu aveți permisiunea de a redeschide acest subiect.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        topic.is_closed = False
        topic.save(update_fields=['is_closed'])
        
        return Response({'message': 'Subiect redeschis cu succes.'})
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Fixează un subiect - doar adminii pot face asta"""
        topic = self.get_object()
        
        # Verifică permisiunile
        if not request.user.is_staff:
            return Response(
                {'error': 'Nu aveți permisiunea de a fixa acest subiect.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        topic.is_pinned = True
        topic.save(update_fields=['is_pinned'])
        
        return Response({'message': 'Subiect fixat cu succes.'})
    
    @action(detail=True, methods=['post'])
    def unpin(self, request, pk=None):
        """Anulează fixarea unui subiect - doar adminii pot face asta"""
        topic = self.get_object()
        
        # Verifică permisiunile
        if not request.user.is_staff:
            return Response(
                {'error': 'Nu aveți permisiunea de a anula fixarea acestui subiect.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        topic.is_pinned = False
        topic.save(update_fields=['is_pinned'])
        
        return Response({'message': 'Fixare anulată cu succes.'})

class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint pentru gestionarea postărilor
    """
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = ForumPagination
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        elif self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer
    
    def get_queryset(self):
        # Filtrează postările după subiect
        topic_id = self.request.query_params.get('topic', None)
        
        queryset = Post.objects.all()
        
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
            
        # Sortare default: cronologic
        return queryset.order_by('created_at')
    
    def perform_create(self, serializer):
        # Obține subiectul din query params
        topic_id = self.request.query_params.get('topic', None)
        if not topic_id:
            return Response(
                {'error': 'Trebuie să specificați subiectul pentru postare.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifică dacă subiectul există și nu este închis
        topic = get_object_or_404(Topic, id=topic_id)
        
        if topic.is_closed:
            return Response(
                {'error': 'Acest subiect este închis și nu permite răspunsuri noi.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Salvează postarea asociată subiectului și utilizatorului curent
        serializer.save(topic=topic, author=self.request.user)
        
        # Actualizează timestamp-ul de activitate pentru subiect
        topic.last_activity = timezone.now()
        topic.save(update_fields=['last_activity'])
        
        # Creează notificări pentru autorul subiectului (dacă nu este același cu autorul postării)
        if topic.author != self.request.user:
            Notification.objects.create(
                user=topic.author,
                topic=topic,
                post=serializer.instance,
                notification_type='new_post'
            )
    
    def create(self, request, *args, **kwargs):
        # Suprascrie metoda create pentru a gestiona cazul în care subiectul este închis
        topic_id = request.query_params.get('topic', None)
        if not topic_id:
            return Response(
                {'error': 'Trebuie să specificați subiectul pentru postare.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        topic = get_object_or_404(Topic, id=topic_id)
        
        if topic.is_closed:
            return Response(
                {'error': 'Acest subiect este închis și nu permite răspunsuri noi.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def mark_solution(self, request, pk=None):
        """Marchează un post ca soluție pentru subiectul său"""
        post = self.get_object()
        topic = post.topic
        
        # Verifică permisiunile
        if not (request.user == topic.author or request.user.is_staff):
            return Response(
                {'error': 'Doar autorul subiectului sau un administrator poate marca o soluție.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Resetează alte soluții din acest subiect
        Post.objects.filter(topic=topic, is_solution=True).update(is_solution=False)
        
        # Marchează această postare ca soluție
        post.is_solution = True
        post.save(update_fields=['is_solution'])
        
        # Notifică autorul postării dacă este diferit de cel care marchează
        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                topic=topic,
                post=post,
                notification_type='solution'
            )
        
        return Response({'message': 'Postare marcată ca soluție cu succes.'})
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Adaugă o reacție la o postare"""
        post = self.get_object()
        reaction_type = request.data.get('reaction_type')
        
        if not reaction_type or reaction_type not in [choice[0] for choice in Reaction.REACTION_TYPES]:
            return Response(
                {'error': 'Tipul de reacție este invalid.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifică dacă utilizatorul a reacționat deja la această postare
        existing_reaction = Reaction.objects.filter(post=post, user=request.user).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # Dacă există deja aceeași reacție, o ștergem
                existing_reaction.delete()
                return Response({'message': 'Reacție ștearsă cu succes.'})
            else:
                # Dacă există o reacție diferită, o actualizăm
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                return Response({'message': 'Reacție actualizată cu succes.'})
        else:
            # Dacă nu există, creăm o reacție nouă
            Reaction.objects.create(
                post=post,
                user=request.user,
                reaction_type=reaction_type
            )
            return Response({'message': 'Reacție adăugată cu succes.'})

class AttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint pentru gestionarea atașamentelor
    """
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        post_id = self.request.query_params.get('post', None)
        if not post_id:
            return Response(
                {'error': 'Trebuie să specificați postarea pentru atașament.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        post = get_object_or_404(Post, id=post_id)
        
        # Verifică dacă utilizatorul are dreptul să adauge atașamente la această postare
        if post.author != self.request.user and not self.request.user.is_staff:
            return Response(
                {'error': 'Nu aveți permisiunea de a adăuga atașamente la această postare.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obține numele și dimensiunea fișierului
        uploaded_file = self.request.FILES.get('file')
        if uploaded_file:
            filename = uploaded_file.name
            file_size = uploaded_file.size
            
            # Determinarea tipului de fișier
            file_type = None
            if '.' in filename:
                extension = filename.split('.')[-1].lower()
                if extension in ['jpg', 'jpeg', 'png', 'gif']:
                    file_type = 'image'
                elif extension in ['pdf', 'doc', 'docx', 'txt']:
                    file_type = 'document'
                elif extension in ['mp4', 'avi', 'mov']:
                    file_type = 'video'
                else:
                    file_type = 'other'
            
            serializer.save(
                post=post,
                filename=filename,
                file_size=file_size,
                file_type=file_type
            )
        else:
            return Response(
                {'error': 'Niciun fișier primit.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def create(self, request, *args, **kwargs):
        # Verificăm dacă fișierul a fost furnizat
        if 'file' not in request.FILES:
            return Response(
                {'error': 'Trebuie să furnizați un fișier pentru atașament.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pentru vizualizarea notificărilor
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Returnează doar notificările utilizatorului autentificat
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marchează o notificare ca citită"""
        notification = self.get_object()
        
        # Verifică dacă notificarea aparține utilizatorului autentificat
        if notification.user != request.user:
            return Response(
                {'error': 'Nu aveți permisiunea de a modifica această notificare.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        
        return Response({'message': 'Notificare marcată ca citită.'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marchează toate notificările unui utilizator ca citite"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'Toate notificările au fost marcate ca citite.'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Returnează numărul de notificări necitite"""
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'count': count})

class SearchView(APIView):
    """
    API endpoint pentru căutare în forum
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        search_term = request.query_params.get('q', None)
        if not search_term or len(search_term) < 3:
            return Response(
                {'error': 'Termenul de căutare trebuie să conțină cel puțin 3 caractere.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Caută subiecte relevante
        topics = Topic.objects.filter(
            (Q(title__icontains=search_term) | Q(content__icontains=search_term)) &
            Q(is_approved=True)
        ).order_by('-last_activity')[:10]  # Limităm la 10 rezultate
        
        # Caută postări relevante
        posts = Post.objects.filter(
            Q(content__icontains=search_term) &
            Q(topic__is_approved=True)
        ).order_by('-created_at')[:10]  # Limităm la 10 rezultate
        
        # Serializăm rezultatele
        topic_serializer = TopicListSerializer(topics, many=True)
        post_serializer = PostListSerializer(posts, many=True)
        
        return Response({
            'topics': topic_serializer.data,
            'posts': post_serializer.data
        })

class ForumStatsView(APIView):
    """
    API endpoint pentru statistici despre forum
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Obține statistici generale despre forum
        topic_count = Topic.objects.filter(is_approved=True).count()
        post_count = Post.objects.count()
        user_count = len(set(list(Topic.objects.values_list('author', flat=True)) + list(Post.objects.values_list('author', flat=True))))
        
        # Obține temele cele mai active - ultimele 5
        recent_topics = Topic.objects.filter(is_approved=True).order_by('-last_activity')[:5]
        
        # Obține temele cu cele mai multe vizualizări
        popular_topics = Topic.objects.filter(is_approved=True).order_by('-views_count')[:5]
        
        # Serializăm datele
        recent_serializer = TopicListSerializer(recent_topics, many=True)
        popular_serializer = TopicListSerializer(popular_topics, many=True)
        
        return Response({
            'stats': {
                'topic_count': topic_count,
                'post_count': post_count,
                'user_count': user_count,
                'last_activity': timezone.now()
            },
            'recent_topics': recent_serializer.data,
            'popular_topics': popular_serializer.data
        })
    
class NewsletterStatusView(APIView):
    """
    API endpoint pentru verificarea statusului abonării la newsletter
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        subscription = NewsletterSubscription.objects.filter(user=user).first()
        
        if subscription:
            return Response({
                'subscribed': subscription.is_active,
                'email': subscription.email
            })
        else:
            # Verifică dacă există un abonament doar cu email (fără user)
            if hasattr(user, 'email') and user.email:
                subscription = NewsletterSubscription.objects.filter(email=user.email).first()
                if subscription:
                    # Asociază abonamentul cu utilizatorul
                    subscription.user = user
                    subscription.save(update_fields=['user'])
                    return Response({
                        'subscribed': subscription.is_active,
                        'email': subscription.email
                    })
            
            return Response({
                'subscribed': False,
                'email': user.email if hasattr(user, 'email') else None
            })

class NewsletterStatusView(APIView):
    """
    API endpoint pentru verificarea statusului abonării la newsletter
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        subscription = NewsletterSubscription.objects.filter(user=user).first()
        
        if subscription:
            return Response({
                'subscribed': subscription.is_active,
                'email': subscription.email
            })
        else:
            # Verifică dacă există un abonament doar cu email (fără user)
            if hasattr(user, 'email') and user.email:
                subscription = NewsletterSubscription.objects.filter(email=user.email).first()
                if subscription:
                    # Asociază abonamentul cu utilizatorul
                    subscription.user = user
                    subscription.save(update_fields=['user'])
                    return Response({
                        'subscribed': subscription.is_active,
                        'email': subscription.email
                    })
            
            return Response({
                'subscribed': False,
                'email': user.email if hasattr(user, 'email') else None
            })

class SubscribeNewsletterView(APIView):
    """
    API endpoint pentru abonarea la newsletter
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Adresa de email este obligatorie.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        # Verifică dacă există deja un abonament pentru acest email
        existing_subscription = NewsletterSubscription.objects.filter(email=email).first()
        
        if existing_subscription:
            # Dacă există dar nu e activ, îl reactivăm
            if not existing_subscription.is_active:
                existing_subscription.is_active = True
                existing_subscription.user = user  # Asociem cu utilizatorul curent
                existing_subscription.save(update_fields=['is_active', 'user'])
                
                # Trimite email de confirmare
                self.send_confirmation_email(email, user)
                
                return Response({'message': 'Abonarea a fost reactivată cu succes.'})
            else:
                return Response(
                    {'message': 'Acest email este deja abonat la newsletter.'},
                    status=status.HTTP_200_OK
                )
        
        # Crează un nou abonament
        subscription = NewsletterSubscription(
            user=user,
            email=email,
            is_active=True
        )
        subscription.save()
        
        # Trimite email de confirmare
        self.send_confirmation_email(email, user)
        
        return Response({'message': 'Abonare realizată cu succes.'}, status=status.HTTP_201_CREATED)
    
    def send_confirmation_email(self, email, user):
        """Trimite email de confirmare a abonării"""
        subject = "Confirmare abonare la newsletter-ul SmartVote"
        
        # Construiește contextul pentru șablon
        context = {
            'user_name': user.get_full_name() if hasattr(user, 'get_full_name') else user.username,
            'app_name': 'SmartVote',
            'current_year': timezone.now().year
        }
        
        # Render șablon HTML
        html_message = render_to_string('newsletter_confirmation.html', context)
        plain_message = strip_tags(html_message)  # Versiune text pentru clienții fără suport HTML
        
        # Trimite email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de confirmare pentru newsletter trimis către: {email}")

class UnsubscribeNewsletterView(APIView):
    """
    API endpoint pentru dezabonarea de la newsletter
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Găsește abonamentele asociate utilizatorului
        subscriptions = NewsletterSubscription.objects.filter(
            Q(user=user) | Q(email=user.email if hasattr(user, 'email') else None)
        )
        
        if subscriptions.exists():
            # Dezactivează toate abonamentele
            subscriptions.update(is_active=False)
            return Response({'message': 'Dezabonare realizată cu succes.'})
        else:
            return Response(
                {'message': 'Nu există abonamente active pentru acest utilizator.'},
                status=status.HTTP_200_OK
            )
        
class NotificationPreferencesView(APIView):
    """
    API endpoint pentru gestionarea preferințelor de notificări
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        preferences, created = NotificationPreferences.objects.get_or_create(user=user)
        
        serializer = NotificationPreferencesSerializer(preferences)
        return Response(serializer.data)
    
    def post(self, request):
        user = request.user
        preferences, created = NotificationPreferences.objects.get_or_create(user=user)
        
        serializer = NotificationPreferencesSerializer(preferences, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Preferințele de notificări au fost actualizate cu succes.',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)