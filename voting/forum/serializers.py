from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Topic, Post, Reaction, Attachment, Notification, NewsletterSubscription, NotificationPreferences

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Serializator de bază pentru informații minime despre utilizator"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        if hasattr(obj, 'first_name') and hasattr(obj, 'last_name'):
            if obj.first_name and obj.last_name:
                return f"{obj.first_name} {obj.last_name}"
            elif obj.first_name:
                return obj.first_name
        return obj.username

class AttachmentSerializer(serializers.ModelSerializer):
    """Serializator pentru atașamente"""
    class Meta:
        model = Attachment
        fields = ['id', 'file', 'filename', 'file_type', 'file_size', 'created_at']

class ReactionSerializer(serializers.ModelSerializer):
    """Serializator pentru reacții"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Reaction
        fields = ['id', 'user', 'reaction_type', 'created_at']

class PostListSerializer(serializers.ModelSerializer):
    """Serializator pentru listarea postărilor"""
    author = UserBasicSerializer(read_only=True)
    reaction_count = serializers.SerializerMethodField()
    has_attachments = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'is_solution', 
            'created_at', 'updated_at', 'reaction_count', 
            'has_attachments'
        ]
    
    def get_reaction_count(self, obj):
        return obj.reactions.count()
    
    def get_has_attachments(self, obj):
        return obj.attachments.exists()

class PostDetailSerializer(serializers.ModelSerializer):
    """Serializator pentru detaliile unei postări"""
    author = UserBasicSerializer(read_only=True)
    reactions = ReactionSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'is_solution', 
            'created_at', 'updated_at', 'reactions',
            'attachments'
        ]

class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializator pentru crearea și actualizarea postărilor"""
    class Meta:
        model = Post
        fields = ['content']

class TopicListSerializer(serializers.ModelSerializer):
    """Serializator pentru listarea subiectelor"""
    author = UserBasicSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    post_count = serializers.SerializerMethodField()
    last_post_date = serializers.SerializerMethodField()
    last_post_author = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'slug', 'author', 'category', 
            'category_name', 'is_pinned', 'is_closed', 
            'views_count', 'created_at', 'last_activity',
            'post_count', 'last_post_date', 'last_post_author'
        ]
    
    def get_post_count(self, obj):
        return obj.posts.count()
    
    def get_last_post_date(self, obj):
        last_post = obj.posts.order_by('-created_at').first()
        return last_post.created_at if last_post else obj.created_at
    
    def get_last_post_author(self, obj):
        last_post = obj.posts.order_by('-created_at').first()
        if last_post:
            return UserBasicSerializer(last_post.author).data
        return UserBasicSerializer(obj.author).data

class TopicDetailSerializer(serializers.ModelSerializer):
    """Serializator pentru detaliile unui subiect"""
    author = UserBasicSerializer(read_only=True)
    category = serializers.SerializerMethodField()
    posts = PostListSerializer(many=True, read_only=True)
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'slug', 'content', 'author', 
            'category', 'is_pinned', 'is_closed', 'is_approved',
            'views_count', 'created_at', 'updated_at', 
            'last_activity', 'posts', 'post_count'
        ]
    
    def get_category(self, obj):
        return {
            'id': obj.category.id,
            'name': obj.category.name,
            'slug': obj.category.slug
        }
    
    def get_post_count(self, obj):
        return obj.posts.count()

class TopicCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializator pentru crearea și actualizarea subiectelor"""
    class Meta:
        model = Topic
        fields = ['title', 'content', 'category']
    
    def create(self, validated_data):
        user = self.context['request'].user
        topic = Topic.objects.create(author=user, **validated_data)
        # Creăm primul post (inițial) din subiect
        Post.objects.create(
            topic=topic,
            author=user,
            content=validated_data.get('content', '')
        )
        return topic

class CategorySerializer(serializers.ModelSerializer):
    """Serializator pentru categorii"""
    topic_count = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()
    last_topic = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 
            'color', 'topic_count', 'post_count', 'last_topic'
        ]
    
    def get_topic_count(self, obj):
        return obj.get_topic_count()
    
    def get_post_count(self, obj):
        return obj.get_post_count()
    
    def get_last_topic(self, obj):
        last_topic = obj.topics.filter(is_approved=True).order_by('-last_activity').first()
        if last_topic:
            return {
                'id': last_topic.id,
                'title': last_topic.title,
                'slug': last_topic.slug,
                'last_activity': last_topic.last_activity,
                'author': UserBasicSerializer(last_topic.author).data
            }
        return None

class NotificationSerializer(serializers.ModelSerializer):
    """Serializator pentru notificări"""
    topic_title = serializers.SerializerMethodField()
    post_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'topic', 'topic_title',
            'post', 'post_preview', 'is_read', 'created_at'
        ]
    
    def get_topic_title(self, obj):
        if obj.topic:
            return obj.topic.title
        elif obj.post and obj.post.topic:
            return obj.post.topic.title
        return None
    
    def get_post_preview(self, obj):
        if obj.post:
            content = obj.post.content
            max_length = 100
            if len(content) > max_length:
                return content[:max_length] + '...'
            return content
        return None
    
class NewsletterSubscriptionSerializer(serializers.ModelSerializer):
    """Serializator pentru abonamentele la newsletter"""
    class Meta:
        model = NewsletterSubscription
        fields = ['id', 'email', 'is_active', 'created_at']

class NotificationPreferencesSerializer(serializers.ModelSerializer):
    """Serializator pentru preferințele de notificări"""
    class Meta:
        model = NotificationPreferences
        fields = ['notify_replies', 'notify_mentions', 'notify_topic_replies']