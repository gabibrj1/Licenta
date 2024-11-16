from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    #salveaza utilizatorul dupa autentificarea sociala
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        
        if not user.is_active:
            user.is_active = True
            user.save()  # salvam modificarile in baza de date
        return user

    # Definim URL-ul de redirectionare dupa autentificarea sociala
    def get_login_redirect_url(self, request):
        user = request.user  #obtinem utilizatorul curent
        
        if user.is_authenticated:
            # generam token-uri JWT pentru utilizatorul autenticat
            refresh = RefreshToken.for_user(user)
            
            # redirectionam cater frontend cu token-urile incluse în URL
            return f"http://localhost:4200/menu?access={refresh.access_token}&refresh={refresh}"
        else:
            # daca utilizatorul nu este autenticat, redirectionam catre pagina de autentificare
            return reverse('auth')
