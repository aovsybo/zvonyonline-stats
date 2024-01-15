from django.urls import path

from .views import WriteDataToGoogleSheet, CreateCallsAPIView


urlpatterns = [
    path('write-call-to-google-sheet', WriteDataToGoogleSheet.as_view()),
    path('create-call', CreateCallsAPIView.as_view()),
]
