from django.urls import path
from . import views


urlpatterns = [
    path('', views.LocationListView.as_view(), name='location_list'),
    path('location/create/', views.LocationCreateView.as_view(), name='location_create'),
    path('location/<int:pk>/', views.InventoryDetailView.as_view(), name='inventory_detail'),
    path('location/<int:pk>/edit/', views.LocationUpdateView.as_view(), name='location_update'),
    path('movements/', views.InventoryMovementListView.as_view(), name='movement_list'),
    path('movements/create/', views.InventoryMovementCreateView.as_view(), name='movement_create'),
    path('movements/transfer/', views.TransferView.as_view(), name='transfer_create'),
    path('location/<int:pk>/correct/', views.InventoryCorrectionView.as_view(), name='inventory_correction'),

    # Products
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Suppliers
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
]
