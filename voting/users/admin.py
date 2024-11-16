from django.contrib import admin
from django.contrib.auth.admin import UserAdmin 
from .models import User

class CustomUserAdmin(UserAdmin):
    #model asociat pt admin
    model = User

    #coloanele care vor fi afisate 
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name')
    #organizarea campurilor in formularul de editare al utiliz
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'cnp', 'address', 'place_of_birth', 'issuing_authority', 'sex', 'series', 'number', 'date_of_issue', 'date_of_expiry')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Verification', {'fields': ('is_verified_by_id', 'verification_code')}),
    )
#inregistrarea modelului de utiliz personalizat in interfata de administrare
admin.site.register(User, CustomUserAdmin)
