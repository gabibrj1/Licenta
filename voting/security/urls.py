from django.urls import path
from .views import (
    SecurityDashboardView, SecurityEventsView, UserSessionsView, 
    TerminateSessionView, SecurityAlertsView, SecurityAnalyticsView,
    CaptchaStatsView, LogCaptchaView, DeviceFingerprintView,
    TrustedDevicesView, AllDevicesView, DeviceFingerprintStatsView
)

urlpatterns = [
    path('dashboard/', SecurityDashboardView.as_view(), name='security-dashboard'),
    path('events/', SecurityEventsView.as_view(), name='security-events'),
    path('sessions/', UserSessionsView.as_view(), name='user-sessions'),
    path('sessions/terminate/', TerminateSessionView.as_view(), name='terminate-session'),
    path('alerts/', SecurityAlertsView.as_view(), name='security-alerts'),
    path('analytics/', SecurityAnalyticsView.as_view(), name='security-analytics'),
    path('captcha/stats/', CaptchaStatsView.as_view(), name='captcha-stats'),
    path('captcha/log/', LogCaptchaView.as_view(), name='log-captcha'),
    path('fingerprint/', DeviceFingerprintView.as_view(), name='device-fingerprint'),
    path('devices/trusted/', TrustedDevicesView.as_view(), name='trusted-devices'),
    path('devices/all/', AllDevicesView.as_view(), name='all-devices'),
    path('devices/stats/', DeviceFingerprintStatsView.as_view(), name='device-stats'),
]