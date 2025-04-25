from django.contrib import admin
from .models import Category, Topic, Post, Reaction, Attachment, Notification

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active', 'get_topic_count', 'get_post_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

class PostInline(admin.TabularInline):
    model = Post
    extra = 0
    fields = ('author', 'content', 'is_solution', 'created_at')
    readonly_fields = ('author', 'created_at')
    can_delete = False
    max_num = 5
    show_change_link = True
    verbose_name = "Răspuns"
    verbose_name_plural = "Răspunsuri"

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at', 'is_pinned', 'is_closed', 'is_approved', 'views_count', 'get_post_count')
    list_filter = ('is_approved', 'is_pinned', 'is_closed', 'category')
    search_fields = ('title', 'content', 'author__username', 'author__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('views_count', 'last_activity')
    inlines = [PostInline]
    actions = ['approve_topics', 'pin_topics', 'unpin_topics', 'close_topics', 'reopen_topics']
    
    def approve_topics(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} subiecte au fost aprobate.')
    approve_topics.short_description = "Aprobă subiectele selectate"
    
    def pin_topics(self, request, queryset):
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'{updated} subiecte au fost fixate.')
    pin_topics.short_description = "Fixează subiectele selectate"
    
    def unpin_topics(self, request, queryset):
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'{updated} subiecte nu mai sunt fixate.')
    unpin_topics.short_description = "Anulează fixarea subiectelor selectate"
    
    def close_topics(self, request, queryset):
        updated = queryset.update(is_closed=True)
        self.message_user(request, f'{updated} subiecte au fost închise.')
    close_topics.short_description = "Închide subiectele selectate"
    
    def reopen_topics(self, request, queryset):
        updated = queryset.update(is_closed=False)
        self.message_user(request, f'{updated} subiecte au fost redeschise.')
    reopen_topics.short_description = "Redeschide subiectele selectate"

class ReactionInline(admin.TabularInline):
    model = Reaction
    extra = 0
    fields = ('user', 'reaction_type', 'created_at')
    readonly_fields = ('user', 'created_at')
    can_delete = True
    max_num = 10
    verbose_name = "Reacție"
    verbose_name_plural = "Reacții"

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    fields = ('file', 'filename', 'file_type', 'file_size', 'created_at')
    readonly_fields = ('filename', 'file_type', 'file_size', 'created_at')
    can_delete = True
    max_num = 5
    verbose_name = "Atașament"
    verbose_name_plural = "Atașamente"

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_topic_title', 'author', 'is_solution', 'created_at', 'get_reaction_count')
    list_filter = ('is_solution', 'created_at')
    search_fields = ('content', 'author__username', 'topic__title')
    date_hierarchy = 'created_at'
    inlines = [ReactionInline, AttachmentInline]
    readonly_fields = ('topic', 'author')
    
    def get_topic_title(self, obj):
        return obj.topic.title
    get_topic_title.short_description = "Subiect"
    
    def get_reaction_count(self, obj):
        return obj.reactions.count()
    get_reaction_count.short_description = "Reacții"

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'reaction_type', 'post', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username', 'post__content')
    date_hierarchy = 'created_at'
    readonly_fields = ('post', 'user')

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'file_type', 'file_size', 'post', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('filename', 'post__content')
    date_hierarchy = 'created_at'
    readonly_fields = ('post', 'filename', 'file_size')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'topic__title')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'topic', 'post')
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notificări au fost marcate ca citite.')
    mark_as_read.short_description = "Marchează notificările selectate ca citite"