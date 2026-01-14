from django.views.generic import ListView, CreateView, TemplateView, UpdateView
from django.urls import reverse_lazy
from .models import Sale
from .forms import SaleForm
from inventory.models import Inventory, InventoryMovement
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Sum, Q
from django.db.models.functions import TruncDay, TruncMonth
from datetime import timedelta
from django.utils import timezone
import json
from django.core.serializers.json import DjangoJSONEncoder

class SaleListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    ordering = ['-day']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search filter
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(customer__name__icontains=q) |
                Q(id__icontains=q)
            )
            
        # Pending payment filter
        status = self.request.GET.get('status')
        if status == 'pending':
            # Filter sales that are NOT marked as paid
            queryset = queryset.filter(is_paid=False)
            
        return queryset

class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/sale_form.html'
    success_url = reverse_lazy('sale_list')

    def form_valid(self, form):
        form.instance.seller = self.request.user
        response = super().form_valid(form)
        sale = self.object

        # Calculate total quantity to subtract
        qty_to_subtract = 0
        if sale.quantity_piece:
            qty_to_subtract = sale.quantity_piece

        if qty_to_subtract > 0 and sale.location:
            with transaction.atomic():
                inventory, _ = Inventory.objects.get_or_create(
                    location=sale.location,
                    defaults={'quantity': 0}
                )
                inventory.quantity -= qty_to_subtract
                inventory.save()
                
                InventoryMovement.objects.create(
                    location=sale.location,
                    quantity=qty_to_subtract,
                    movement_type='VENTA',
                    date=sale.day # Or auto_now_add
                )

        return response

class SaleUpdateView(LoginRequiredMixin, UpdateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/sale_form.html'
    success_url = reverse_lazy('sale_list')

class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date range: Last 30 days for trends
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # 1. Sales Trend (Last 30 days)
        sales_trend = Sale.objects.filter(day__range=[start_date, end_date])\
            .annotate(date=TruncDay('day'))\
            .values('date')\
            .annotate(total=Sum('price'))\
            .order_by('date')
        
        trend_labels = [entry['date'].strftime('%Y-%m-%d') for entry in sales_trend]
        trend_data = [float(entry['total']) for entry in sales_trend]

        # 2. Payment Methods
        payment_methods = Sale.objects.filter(day__range=[start_date, end_date])\
            .values('payment_method')\
            .annotate(total=Sum('price'))
        
        payment_labels = [entry['payment_method'] for entry in payment_methods]
        payment_data = [float(entry['total']) for entry in payment_methods]

        # 3. Top Customers
        top_customers = Sale.objects.filter(day__range=[start_date, end_date])\
            .values('customer__name')\
            .annotate(total=Sum('price'))\
            .order_by('-total')[:5]
            
        customer_labels = [entry['customer__name'] for entry in top_customers]
        customer_data = [float(entry['total']) for entry in top_customers]

        # 4. Sales by Seller per Month (All time or last year)
        # Group by Month and Seller
        seller_sales = Sale.objects.annotate(month=TruncMonth('day'))\
            .values('month', 'seller__username')\
            .annotate(total=Sum('price'))\
            .order_by('-month', 'seller__username')

        context['trend_labels'] = json.dumps(trend_labels, cls=DjangoJSONEncoder)
        context['trend_data'] = json.dumps(trend_data, cls=DjangoJSONEncoder)
        context['payment_labels'] = json.dumps(payment_labels, cls=DjangoJSONEncoder)
        context['payment_data'] = json.dumps(payment_data, cls=DjangoJSONEncoder)
        context['customer_labels'] = json.dumps(customer_labels, cls=DjangoJSONEncoder)
        context['customer_data'] = json.dumps(customer_data, cls=DjangoJSONEncoder)
        context['seller_sales'] = seller_sales

        return context