from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    
    path('api/', include('users.urls')),  
    path('accounts/', include('allauth.urls')),  
    path('api/menu/', include('menu.urls')),
    path('api/', include('vote.urls')),
    path('api/', include('news.urls')),
    path('api/forum/', include('forum.urls')),
    path('api/presidential-candidates/', include('presidential_candidates.urls')),
    path('api/local-candidates/', include('local_candidates.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

