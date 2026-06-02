import calendar
from django.views.generic import ListView, CreateView, TemplateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from .models import Sale, Order
from .forms import SaleForm, OrderForm
from inventory.models import Inventory, InventoryMovement
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, models
from django.db.models import Sum, Q, Avg, Count
from django.db.models.functions import TruncDay, TruncMonth
from datetime import timedelta, date
from django.utils import timezone
import json
from django.core.serializers.json import DjangoJSONEncoder
from expenses.models import Expense
from django.contrib.auth import get_user_model
from django.contrib import messages

class SaleListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    ordering = ['-day']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(customer__name__icontains=q) | Q(id__icontains=q))
        status = self.request.GET.get('status')
        if status == 'pending':
            queryset = queryset.filter(Q(is_paid=False) & Q(amount_paid__lt=models.F('price')))
        seller_id = self.request.GET.get('seller')
        if seller_id and seller_id.isdigit():
            queryset = queryset.filter(seller_id=seller_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        context['sellers'] = User.objects.all()
        context['selected_seller'] = self.request.GET.get('seller', '')
        return context

class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/sale_form.html'
    success_url = reverse_lazy('sale_list')

    def form_valid(self, form):
        form.instance.seller = self.request.user
        response = super().form_valid(form)
        sale = self.object
        qty_to_subtract = sale.quantity_piece if sale.quantity_piece else 0
        if qty_to_subtract > 0 and sale.location:
            with transaction.atomic():
                inventory, _ = Inventory.objects.get_or_create(location=sale.location, defaults={'quantity': 0})
                inventory.quantity -= qty_to_subtract
                inventory.save()
                InventoryMovement.objects.create(location=sale.location, quantity=qty_to_subtract, movement_type='VENTA', date=sale.day)
        return response

class SaleUpdateView(LoginRequiredMixin, UpdateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/sale_form.html'
    success_url = reverse_lazy('sale_list')

    def form_valid(self, form):
        old_sale = Sale.objects.get(pk=self.object.pk)
        response = super().form_valid(form)
        new_sale = self.object
        with transaction.atomic():
            old_qty = old_sale.quantity_piece if old_sale.quantity_piece else 0
            if old_sale.location and old_qty > 0:
                inv_old, _ = Inventory.objects.get_or_create(location=old_sale.location, defaults={'quantity': 0})
                inv_old.quantity += old_qty
                inv_old.save()
            new_qty = new_sale.quantity_piece if new_sale.quantity_piece else 0
            if new_sale.location and new_qty > 0:
                inv_new, _ = Inventory.objects.get_or_create(location=new_sale.location, defaults={'quantity': 0})
                inv_new.quantity -= new_qty
                inv_new.save()
        return response

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'sales/order_list.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        return Order.objects.filter(status='PENDIENTE').order_by('-created_at')

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'sales/order_form.html'
    success_url = reverse_lazy('order_list')

    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)

@transaction.atomic
def complete_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status != 'PENDIENTE':
        messages.error(request, "Este pedido ya no está pendiente.")
        return redirect('order_list')
    
    # Convert to Sale
    sale = Sale.objects.create(
        day=timezone.now().date(),
        customer=order.customer,
        location=order.location,
        sale_type=order.sale_type,
        quantity_kg=order.quantity_kg,
        quantity_piece=order.quantity_piece,
        unit_price=order.unit_price,
        price=order.total_price,
        amount_paid=order.total_price,
        is_paid=True,
        payment_date=timezone.now().date(),
        seller=order.seller,
        payment_method=order.payment_method
    )
    
    # Update Inventory
    qty_to_subtract = sale.quantity_piece if sale.quantity_piece else 0
    if qty_to_subtract > 0 and sale.location:
        inventory, _ = Inventory.objects.get_or_create(location=sale.location, defaults={'quantity': 0})
        inventory.quantity -= qty_to_subtract
        inventory.save()
        InventoryMovement.objects.create(location=sale.location, quantity=qty_to_subtract, movement_type='VENTA', date=sale.day)
    
    order.status = 'COMPLETADO'
    order.save()
    
    messages.success(request, f"Pedido #{order.id} convertido en venta exitosamente.")
    return redirect('sale_list')

class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Month Selection
        selected_month_str = self.request.GET.get('month')
        if selected_month_str:
            try:
                year, month = map(int, selected_month_str.split('-'))
                view_date = date(year, month, 1)
            except ValueError:
                view_date = timezone.now().date().replace(day=1)
        else:
            view_date = timezone.now().date().replace(day=1)
            
        month_start = view_date
        month_end = view_date.replace(day=calendar.monthrange(view_date.year, view_date.month)[1])
        
        # 1. Sales Trend (Selected Month)
        sales_trend = Sale.objects.filter(day__range=[month_start, month_end])\
            .annotate(date=TruncDay('day'))\
            .values('date')\
            .annotate(total=Sum('price'))\
            .order_by('date')
        
        trend_labels = [entry['date'].strftime('%Y-%m-%d') for entry in sales_trend]
        trend_data = [float(entry['total']) for entry in sales_trend]

        # 2. Payment Methods (Selected Month)
        payment_methods = Sale.objects.filter(day__range=[month_start, month_end])\
            .values('payment_method')\
            .annotate(total=Sum('price'))
        
        payment_labels = [entry['payment_method'] for entry in payment_methods]
        payment_data = [float(entry['total']) for entry in payment_methods]

        # 3. Top Customers (Selected Month)
        top_customers = Sale.objects.filter(day__range=[month_start, month_end])\
            .values('customer__name')\
            .annotate(total=Sum('price'))\
            .order_by('-total')[:5]
            
        customer_labels = [entry['customer__name'] for entry in top_customers]
        customer_data = [float(entry['total']) for entry in top_customers]

        # 4. Sales by Seller (Selected Month)
        seller_sales = Sale.objects.filter(day__range=[month_start, month_end])\
            .values('seller__username')\
            .annotate(total=Sum('price'))\
            .order_by('seller__username')

        # 5. Expenses & Profit (Selected Month)
        total_sales_month = Sale.objects.filter(day__range=[month_start, month_end])\
            .aggregate(Sum('price'))['price__sum'] or 0
        total_expenses_month = Expense.objects.filter(date__range=[month_start, month_end])\
            .aggregate(Sum('amount'))['amount__sum'] or 0
        net_profit_month = total_sales_month - total_expenses_month
        
        context['total_sales_month'] = total_sales_month
        context['total_expenses_month'] = total_expenses_month
        context['net_profit_month'] = net_profit_month

        # Egg production and sales for selected month
        eggs_produced_month = InventoryMovement.objects.filter(
            movement_type='PRODUCCION',
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0

        eggs_sold_pieces_month = Sale.objects.filter(
            day__range=[month_start, month_end]
        ).aggregate(Sum('quantity_piece'))['quantity_piece__sum'] or 0

        eggs_sold_kg_month = float(Sale.objects.filter(
            day__range=[month_start, month_end]
        ).aggregate(Sum('quantity_kg'))['quantity_kg__sum'] or 0)

        context['eggs_produced_month'] = eggs_produced_month
        context['eggs_sold_pieces_month'] = eggs_sold_pieces_month
        context['eggs_sold_kg_month'] = eggs_sold_kg_month
        context['trend_labels'] = json.dumps(trend_labels, cls=DjangoJSONEncoder)
        context['trend_data'] = json.dumps(trend_data, cls=DjangoJSONEncoder)
        context['payment_labels'] = json.dumps(payment_labels, cls=DjangoJSONEncoder)
        context['payment_data'] = json.dumps(payment_data, cls=DjangoJSONEncoder)
        context['customer_labels'] = json.dumps(customer_labels, cls=DjangoJSONEncoder)
        context['customer_data'] = json.dumps(customer_data, cls=DjangoJSONEncoder)
        context['seller_sales'] = seller_sales
        context['view_date'] = view_date

        # Available Months for Dropdown (Only months with data)
        # Get months with sales
        sales_months = Sale.objects.annotate(month=TruncMonth('day')).values_list('month', flat=True).distinct()
        # Get months with expenses
        expenses_months = Expense.objects.annotate(month=TruncMonth('date')).values_list('month', flat=True).distinct()
        
        # Combine and sort
        all_months = sorted(list(set(list(sales_months) + list(expenses_months))), reverse=True)
        
        # Ensure current month is always included if not present
        current_month = timezone.now().date().replace(day=1)
        if current_month not in all_months:
            all_months.insert(0, current_month)
            all_months.sort(reverse=True)

        available_months = []
        month_names_es = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }

        for d in all_months:
            if d: # Handle potential None
                available_months.append({
                    'value': d.strftime('%Y-%m'),
                    'label': f"{month_names_es[d.month]} {d.year}"
                })
        
        context['available_months'] = available_months

        # 6. Monthly Financial Report (Show all months with data)
        monthly_financial_data = []
        monthly_category_expenses = {}

        # Limit historical report to last 12 months with data for performance
        report_months = available_months[:12]

        for am in reversed(report_months):
            y, m = map(int, am['value'].split('-'))
            ms = date(y, m, 1)
            me = ms.replace(day=calendar.monthrange(y, m)[1])

            s_m = Sale.objects.filter(day__range=[ms, me]).aggregate(Sum('price'))['price__sum'] or 0
            e_m = Expense.objects.filter(date__range=[ms, me]).aggregate(Sum('amount'))['amount__sum'] or 0

            eggs_prod_m = InventoryMovement.objects.filter(
                movement_type='PRODUCCION',
                date__gte=ms,
                date__lte=me
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0
            eggs_sold_p_m = Sale.objects.filter(day__range=[ms, me]).aggregate(
                Sum('quantity_piece'))['quantity_piece__sum'] or 0
            eggs_sold_k_m = float(Sale.objects.filter(day__range=[ms, me]).aggregate(
                Sum('quantity_kg'))['quantity_kg__sum'] or 0)

            monthly_financial_data.append({
                'month': am['label'],
                'total_sales': s_m,
                'total_expenses': e_m,
                'net_profit': s_m - e_m,
                'eggs_produced': eggs_prod_m,
                'eggs_sold_pieces': eggs_sold_p_m or 0,
                'eggs_sold_kg': eggs_sold_k_m,
            })

            cat_exp = Expense.objects.filter(date__range=[ms, me]).values('category').annotate(total=Sum('amount'))
            monthly_category_expenses[am['label']] = {entry['category']: float(entry['total']) for entry in cat_exp}
        
        context['monthly_financial_data'] = monthly_financial_data
        context['monthly_financial_json'] = json.dumps(monthly_financial_data, cls=DjangoJSONEncoder)
        context['monthly_category_expenses'] = json.dumps(monthly_category_expenses, cls=DjangoJSONEncoder)

        return context


class InvestorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/investor_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        month_names_es = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }

        # Get all months that have sales or expense data
        sales_months = Sale.objects.annotate(month=TruncMonth('day')).values_list('month', flat=True).distinct()
        expenses_months = Expense.objects.annotate(month=TruncMonth('date')).values_list('month', flat=True).distinct()
        all_months_raw = sorted(
            set(list(sales_months) + list(expenses_months)),
            reverse=True
        )
        all_months_raw = [d for d in all_months_raw if d]

        # Limit to last 12 months for display
        report_months_raw = all_months_raw[:12]

        # Build monthly data in chronological order (oldest → newest)
        monthly_data = []
        for d in reversed(report_months_raw):
            ms = date(d.year, d.month, 1)
            me = ms.replace(day=calendar.monthrange(ms.year, ms.month)[1])

            s = float(Sale.objects.filter(day__range=[ms, me]).aggregate(Sum('price'))['price__sum'] or 0)
            e = float(Expense.objects.filter(date__range=[ms, me]).aggregate(Sum('amount'))['amount__sum'] or 0)
            p = s - e

            eggs_prod = InventoryMovement.objects.filter(
                movement_type='PRODUCCION',
                date__gte=ms,
                date__lte=me
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0

            monthly_data.append({
                'month': f"{month_names_es[ms.month]} {ms.year}",
                'sales': s,
                'expenses': e,
                'profit': p,
                'eggs_produced': eggs_prod,
            })

        # Only use months with BOTH sales and expenses for KPI averages.
        # Months missing either (e.g. no expenses registered) would skew profit/margin.
        complete_months = [m for m in monthly_data if m['sales'] > 0 and m['expenses'] > 0]
        months_of_data = len(complete_months)

        if complete_months:
            avg_monthly_sales = sum(m['sales'] for m in complete_months) / len(complete_months)
            avg_monthly_expenses = sum(m['expenses'] for m in complete_months) / len(complete_months)
            avg_monthly_profit = sum(m['profit'] for m in complete_months) / len(complete_months)
            profit_margin_pct = (avg_monthly_profit / avg_monthly_sales * 100) if avg_monthly_sales > 0 else 0

            growth_rates = []
            for i in range(1, len(complete_months)):
                prev_s = complete_months[i - 1]['sales']
                curr_s = complete_months[i]['sales']
                if prev_s > 0:
                    growth_rates.append((curr_s - prev_s) / prev_s * 100)
            avg_monthly_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        else:
            avg_monthly_sales = avg_monthly_expenses = avg_monthly_profit = 0
            profit_margin_pct = avg_monthly_growth = 0

        # Totals across all available history (not just last 12 months)
        total_customers = Sale.objects.values('customer').distinct().count()

        total_eggs_produced = InventoryMovement.objects.filter(
            movement_type='PRODUCCION'
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0

        total_eggs_sold_pieces = Sale.objects.aggregate(
            Sum('quantity_piece'))['quantity_piece__sum'] or 0

        # Data date range
        first_sale = Sale.objects.order_by('day').first()
        data_start = first_sale.day if first_sale else timezone.now().date()

        context.update({
            'months_of_data': months_of_data,
            'avg_monthly_sales': avg_monthly_sales,
            'avg_monthly_expenses': avg_monthly_expenses,
            'avg_monthly_profit': avg_monthly_profit,
            'profit_margin_pct': profit_margin_pct,
            'avg_monthly_growth': avg_monthly_growth,
            'total_customers': total_customers,
            'total_eggs_produced': total_eggs_produced,
            'total_eggs_sold_pieces': total_eggs_sold_pieces,
            'monthly_data': monthly_data,
            'monthly_data_json': json.dumps(monthly_data, cls=DjangoJSONEncoder),
            'avg_monthly_profit_float': float(avg_monthly_profit),
            'data_start': data_start,
            'data_end': timezone.now().date(),
        })

        return context
