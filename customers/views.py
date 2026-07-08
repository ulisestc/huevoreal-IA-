from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from .models import Customer, Fraccionamiento, Zona
from .forms import CustomerForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    ordering = ['first_name', 'last_name']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(first_name__icontains=q) | 
                Q(last_name__icontains=q) | 
                Q(phone_number__icontains=q) |
                Q(fraccionamiento__name__icontains=q) |
                Q(zona__name__icontains=q)
            )
        return queryset

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    template_name = 'customers/customer_form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    template_name = 'customers/customer_form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')

class FraccionamientoCreateAPIView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'El nombre no puede estar vacío.'}, status=400)
        
        # Avoid duplicates (case-insensitive checking could also be nice, but get_or_create is default)
        # To avoid case duplicates, let's check with iexact
        if Fraccionamiento.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Este fraccionamiento ya existe.'}, status=400)
            
        frac = Fraccionamiento.objects.create(name=name)
        return JsonResponse({'success': True, 'id': frac.id, 'name': frac.name})

class ZonaCreateAPIView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'El nombre no puede estar vacío.'}, status=400)
        
        if Zona.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Esta zona ya existe.'}, status=400)
            
        zona = Zona.objects.create(name=name)
        return JsonResponse({'success': True, 'id': zona.id, 'name': zona.name})
