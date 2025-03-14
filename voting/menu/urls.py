from django.urls import path
from .views import UserProfileView, ContactInfoView, MapInfoView
from .views import send_contact_message, schedule_appointment, confirm_appointment, reject_appointment, check_availability

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('contact/', ContactInfoView.as_view(), name='contact-info'),
    path('send-contact/', send_contact_message, name='send_contact'),
    path('appointments/schedule/', schedule_appointment, name='schedule-appointment'),
    path('appointments/confirm/<str:token>/', confirm_appointment, name='confirm-appointment'),
    path('appointments/reject/<str:token>/', reject_appointment, name='reject-appointment'),
    path('appointments/availability/<str:date>/', check_availability, name='check-availability'),
    path('map/', MapInfoView.as_view(), name='map-info'),

]
