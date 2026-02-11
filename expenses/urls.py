from django.urls import path
from .views import ExpenseListView, ExpenseCreateView, ExpenseUpdateView, ExpenseDeleteView

urlpatterns = [
    path('', ExpenseListView.as_view(), name='expense_list'),
    path('add/', ExpenseCreateView.as_view(), name='expense_add'),
    path('<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense_edit'),
    path('<int:pk>/delete/', ExpenseDeleteView.as_view(), name='expense_delete'),
]
