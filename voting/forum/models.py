from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    """Model pentru categoriile de forum"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Numele icon-ului (ex: 'fa-comments')")
    color = models.CharField(max_length=20, blank=True, null=True, help_text="Codul de culoare (ex: '#3498db')")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Categorie Forum"
        verbose_name_plural = "Categorii Forum"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_topic_count(self):
        return self.topics.filter(is_approved=True).count()
    
    def get_post_count(self):
        return Post.objects.filter(topic__category=self, topic__is_approved=True).count()

class Topic(models.Model):
    """Model pentru subiectele din forum"""
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='topics')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_topics')
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Subiect"
        verbose_name_plural = "Subiecte"
        ordering = ['-is_pinned', '-last_activity']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            # Verifică dacă slug-ul există deja
            while Topic.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        # Actualizează last_activity doar la crearea inițială
        if not self.pk:
            self.last_activity = timezone.now()
            
        super().save(*args, **kwargs)
    
    def get_post_count(self):
        return self.posts.count()

class Post(models.Model):
    """Model pentru postări/răspunsuri"""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField()
    is_solution = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Postare"
        verbose_name_plural = "Postări"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Răspuns de {self.author.username} la {self.topic.title}"
    
    def save(self, *args, **kwargs):
        # Actualizează last_activity din topic la fiecare postare nouă
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.topic.last_activity = timezone.now()
            self.topic.save(update_fields=['last_activity'])

class Reaction(models.Model):
    """Model pentru reacții la postări"""
    REACTION_TYPES = (
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('helpful', 'Helpful'),
        ('insightful', 'Insightful'),
    )
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Reacție"
        verbose_name_plural = "Reacții"
        # Un utilizator poate avea doar o reacție per postare
        unique_together = ('post', 'user')
    
    def __str__(self):
        return f"{self.user.username}: {self.get_reaction_type_display()} pentru postarea #{self.post.id}"

class Attachment(models.Model):
    """Model pentru atașamente la postări"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='forum/attachments/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    file_size = models.IntegerField(default=0)  # Mărimea în bytes
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Atașament"
        verbose_name_plural = "Atașamente"
    
    def __str__(self):
        return self.filename

class Notification(models.Model):
    """Model pentru notificări de forum"""
    NOTIFICATION_TYPES = (
        ('new_post', 'Răspuns nou'),
        ('mention', 'Menționare'),
        ('solution', 'Soluție marcată'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_notifications')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Notificare"
        verbose_name_plural = "Notificări"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notificare pentru {self.user.username}: {self.get_notification_type_display()}"
    
class NewsletterSubscription(models.Model):
    """Model pentru abonatii la newsletter"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='newsletter_subscriptions', null=True, blank=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Abonament Newsletter"
        verbose_name_plural = "Abonamente Newsletter"
    
    def __str__(self):
        return self.email
    
class NotificationPreferences(models.Model):
    """Model pentru preferințele de notificări"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notify_replies = models.BooleanField(default=True)
    notify_mentions = models.BooleanField(default=True)
    notify_topic_replies = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Preferințe Notificări"
        verbose_name_plural = "Preferințe Notificări"
    
    def __str__(self):
        return f"Preferințe notificări pentru {self.user.username}"