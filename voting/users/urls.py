from django.urls import path
from . import views
from .views import RegisterView, VerifyEmailView,UploadIdView
from .views import social_login_redirect
from .views import AutofillDataView
from .views import send_feedback
from .views import SocialLoginCallbackView
from .views import LoginView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('upload-id/', UploadIdView.as_view(), name='upload_id'),
     path('autofill-data/', AutofillDataView.as_view(), name='autofill_data'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms_of_service', views.terms_of_service, name='terms_of_service'),
    path('accounts/google/login/', social_login_redirect, {'provider': 'Google'}, name='google_login_redirect'),
    path('accounts/facebook/login/', social_login_redirect, {'provider': 'Facebook'}, name='facebook_login_redirect'),
    path('send-feedback/', send_feedback, name='send_ffedback'),
    path('social-login/callback/', SocialLoginCallbackView.as_view(), name='social-login-callback'),
    path('login/', LoginView.as_view(), name='login'),
]
