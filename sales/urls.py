from django.urls import path
from . import views


urlpatterns = [
    path('', views.SaleListView.as_view(), name='sale_list'),
    path('create/', views.SaleCreateView.as_view(), name='sale_create'),
    path('<int:pk>/edit/', views.SaleUpdateView.as_view(), name='sale_update'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    
    # Orders
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/complete/', views.complete_order, name='order_complete'),
]
