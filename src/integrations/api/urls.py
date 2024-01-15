from django.urls import path

from .views import PostDataToTable


urlpatterns = [
    path('', PostDataToTable.as_view()),
]
