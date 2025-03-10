from django.urls import path
from .views import UserProfileView, ContactInfoView
from .views import send_contact_message

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('contact/', ContactInfoView.as_view(), name='contact-info'),
    path('send-contact/', send_contact_message, name='send_contact'),
]
