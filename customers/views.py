from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Customer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | 
                Q(phone_number__icontains=q)
            )
        return queryset

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    template_name = 'customers/customer_form.html'
    fields = ['name', 'address', 'phone_number']
    success_url = reverse_lazy('customer_list')

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    template_name = 'customers/customer_form.html'
    fields = ['name', 'address', 'phone_number']
    success_url = reverse_lazy('customer_list')

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')
