from django.urls import path

from .views import WriteDataToGoogleSheet, TestAPI


urlpatterns = [
    path('write-call-to-google-sheet', WriteDataToGoogleSheet.as_view()),
    path('tests', TestAPI.as_view()),
]
