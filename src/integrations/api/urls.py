from django.urls import path

from .views import WriteDataToGoogleSheet, Test


urlpatterns = [
    path('write-call-to-google-sheet', WriteDataToGoogleSheet.as_view()),
    path('tests', Test.as_view()),
]
