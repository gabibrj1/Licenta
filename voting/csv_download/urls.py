from django.urls import path
from .views import CSVDownloadView, CSVDownloadStatusView

urlpatterns = [
    path('download/', CSVDownloadView.as_view(), name='csv-download'),
    path('status/', CSVDownloadStatusView.as_view(), name='csv-download-status'),
]