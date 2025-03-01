from django.urls import path
from . import views
from .views import RegisterView, VerifyEmailView,UploadIdView
from .views import social_login_redirect
from .views import AutofillDataView, AutofillScanDataView
from .views import send_feedback
from .views import SocialLoginCallbackView
from .views import LoginView
from .views import ScanIdView
from .views import DetectIDCardView
from .views import ManipulateImageView
from .views import ValidateLocalityView
from .views import FaceRecognitionView
from .views import RegisterWithIDCardView
from .views import LoginWithIDCardView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('upload-id/', UploadIdView.as_view(), name='upload_id'),
     path('autofill_data/', AutofillDataView.as_view(), name='autofill_data/'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms_of_service', views.terms_of_service, name='terms_of_service'),
    path('accounts/google/login/', social_login_redirect, {'provider': 'Google'}, name='google_login_redirect'),
    path('accounts/facebook/login/', social_login_redirect, {'provider': 'Facebook'}, name='facebook_login_redirect'),
    path('send-feedback/', send_feedback, name='send_ffedback'),
    path('social-login/callback/', SocialLoginCallbackView.as_view(), name='social-login-callback'),
    path('login/', LoginView.as_view(), name='login'),
    path('check-profanity/', views.check_profanity, name='check_profanity'),
    path('scan-id/', ScanIdView.as_view(), name='scan_id'),
    path('autofill-scan-data/', AutofillScanDataView.as_view(), name='autofill-scan-data'),
    path('detect-id-card/', DetectIDCardView.as_view(), name='detect_id_card'),
    path('manipulate-image/', ManipulateImageView.as_view(), name='manipulate-image'),
    path('validate-locality/', ValidateLocalityView.as_view(), name='validate-locality'),
    path('face-recognition/', FaceRecognitionView.as_view(), name='face-recognition'),
    path('register-with-id-card/', RegisterWithIDCardView.as_view(), name='register-with-id-card'),
    path('login-id-card/', LoginWithIDCardView.as_view(), name='login-id-card'),

]
