from django.urls import path

from .views import PostDataToTable, CallsAPIView


urlpatterns = [
    path('', PostDataToTable.as_view()),
    path('calls', CallsAPIView.as_view()),
]
