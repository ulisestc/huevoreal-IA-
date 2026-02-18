from django.views.generic import ListView, DetailView, CreateView, FormView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from .models import Location, Inventory, InventoryMovement
from .forms import InventoryMovementForm, InventoryCorrectionForm
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'inventory/location_list.html'
    context_object_name = 'locations'
    paginate_by = 10

class LocationCreateView(LoginRequiredMixin, CreateView):
    model = Location
    template_name = 'inventory/location_form.html'
    fields = ['name']
    success_url = reverse_lazy('location_list')

class InventoryDetailView(LoginRequiredMixin, DetailView):
    model = Location
    template_name = 'inventory/inventory_detail.html'
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inventory'] = Inventory.objects.filter(location=self.object).first()
        context['movements'] = InventoryMovement.objects.filter(location=self.object).order_by('-date')
        return context

class InventoryMovementListView(LoginRequiredMixin, ListView):
    model = InventoryMovement
    template_name = 'inventory/movement_list.html'
    context_object_name = 'movements'
    ordering = ['-date']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(location__name__icontains=q) | 
                Q(movement_type__icontains=q)
            )
        return queryset

class InventoryMovementCreateView(LoginRequiredMixin, CreateView):
    model = InventoryMovement
    form_class = InventoryMovementForm
    template_name = 'inventory/movement_form.html'
    success_url = reverse_lazy('movement_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        movement = self.object
        inventory, created = Inventory.objects.get_or_create(
            location=movement.location,
            defaults={'quantity': 0}
        )

        if movement.movement_type == 'PRODUCCION':
            inventory.quantity += movement.quantity
        
        inventory.save()
        return response

class TransferForm(forms.Form):
    source_location = forms.ModelChoiceField(queryset=Location.objects.all(), label="Desde", widget=forms.Select(attrs={'class': 'form-select form-select-lg'}))
    dest_location = forms.ModelChoiceField(queryset=Location.objects.all(), label="Hacia", widget=forms.Select(attrs={'class': 'form-select form-select-lg'}))
    quantity = forms.IntegerField(label="Cantidad", widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg'}))

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source_location')
        dest = cleaned_data.get('dest_location')
        if source == dest:
            raise forms.ValidationError("La ubicación de origen y destino no pueden ser la misma.")
        return cleaned_data

class TransferView(LoginRequiredMixin, FormView):
    template_name = 'inventory/transfer_form.html'
    form_class = TransferForm
    success_url = reverse_lazy('movement_list')

    def form_valid(self, form):
        source = form.cleaned_data['source_location']
        dest = form.cleaned_data['dest_location']
        quantity = form.cleaned_data['quantity']

        with transaction.atomic():
            # Source - OUT
            inv_source, _ = Inventory.objects.get_or_create(location=source, defaults={'quantity': 0})
            inv_source.quantity -= quantity
            inv_source.save()
            InventoryMovement.objects.create(
                location=source,
                quantity=quantity,
                movement_type='TRASPASO_SALIDA'
            )

            # Dest - IN
            inv_dest, _ = Inventory.objects.get_or_create(location=dest, defaults={'quantity': 0})
            inv_dest.quantity += quantity
            inv_dest.save()
            InventoryMovement.objects.create(
                location=dest,
                quantity=quantity,
                movement_type='TRASPASO_ENTRADA'
            )
        
        return super().form_valid(form)

class InventoryCorrectionView(LoginRequiredMixin, FormView):
    template_name = 'inventory/correction_form.html'
    form_class = InventoryCorrectionForm

    def dispatch(self, request, *args, **kwargs):
        self.location = get_object_or_404(Location, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location'] = self.location
        inventory = Inventory.objects.filter(location=self.location).first()
        context['current_quantity'] = inventory.quantity if inventory else 0
        return context
    
    def form_valid(self, form):
        real_quantity = form.cleaned_data['real_quantity']
        inventory, _ = Inventory.objects.get_or_create(location=self.location, defaults={'quantity': 0})
        
        diff = real_quantity - inventory.quantity
        
        if diff != 0:
            with transaction.atomic():
                inventory.quantity = real_quantity
                inventory.save()
                
                InventoryMovement.objects.create(
                    location=self.location,
                    quantity=diff,
                    movement_type='CORRECCION',
                    date=timezone.now()
                )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('inventory_detail', kwargs={'pk': self.location.pk})