from django.urls import path
from . import views


urlpatterns = [
    path('', views.SaleListView.as_view(), name='sale_list'),
    path('create/', views.SaleCreateView.as_view(), name='sale_create'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
]
