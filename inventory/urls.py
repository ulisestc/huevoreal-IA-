from django.urls import path
from . import views


urlpatterns = [
    path('', views.LocationListView.as_view(), name='location_list'),
    path('location/create/', views.LocationCreateView.as_view(), name='location_create'),
    path('location/<int:pk>/', views.InventoryDetailView.as_view(), name='inventory_detail'),
    path('movements/', views.InventoryMovementListView.as_view(), name='movement_list'),
    path('movements/create/', views.InventoryMovementCreateView.as_view(), name='movement_create'),
    path('movements/transfer/', views.TransferView.as_view(), name='transfer_create'),
]
