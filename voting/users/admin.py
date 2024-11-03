from django.contrib import admin
from django.contrib.auth.admin import UserAdmin 
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'cnp', 'address', 'place_of_birth', 'issuing_authority', 'sex', 'series', 'number', 'date_of_issue', 'date_of_expiry')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Verification', {'fields': ('is_verified_by_id', 'verification_code')}),
    )

admin.site.register(User, CustomUserAdmin)
