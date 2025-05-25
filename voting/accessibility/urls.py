from django.urls import path
from .views import AccessibilitySettingsView, AccessibilityTestView, AccessibilityInfoView

urlpatterns = [
    path('settings/', AccessibilitySettingsView.as_view(), name='accessibility-settings'),
    path('test/', AccessibilityTestView.as_view(), name='accessibility-test'),
    path('info/', AccessibilityInfoView.as_view(), name='accessibility-info'),
]