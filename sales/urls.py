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
    path('orders/<int:pk>/cancel/', views.cancel_order, name='order_cancel'),

    # Recurring Orders
    path('recurring/', views.RecurringOrderListView.as_view(), name='recurring_order_list'),
    path('recurring/create/', views.RecurringOrderCreateView.as_view(), name='recurring_order_create'),
    path('recurring/<int:pk>/edit/', views.RecurringOrderUpdateView.as_view(), name='recurring_order_update'),
    path('recurring/<int:pk>/delete/', views.RecurringOrderDeleteView.as_view(), name='recurring_order_delete'),
    path('recurring/generate/', views.generate_recurring_orders_view, name='generate_recurring_orders'),
    path('recurring/generate-list/', views.RecurringOrderGenerateView.as_view(), name='recurring_order_generate_list'),

    # Routes
    path('routes/', views.RouteOptimizerView.as_view(), name='route_optimizer'),



    # Investor Dashboard
    path('inversores/', views.InvestorDashboardView.as_view(), name='investor_dashboard'),
]
