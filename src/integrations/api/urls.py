from django.urls import path

from .views import WriteDataToGoogleSheet


urlpatterns = [
    path('write-call-to-google-sheet', WriteDataToGoogleSheet.as_view()),
]
