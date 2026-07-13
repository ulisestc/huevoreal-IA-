import calendar
from django.views.generic import ListView, CreateView, TemplateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from .models import Sale, Order, RecurringOrder
from .forms import SaleForm, OrderForm, RecurringOrderForm
from inventory.models import Inventory, InventoryMovement, Product, Location
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, models
from django.db.models import Sum, Q, Avg, Count, Value
from django.db.models.functions import TruncDay, TruncMonth, Concat
from datetime import timedelta, date
from django.utils import timezone
from decimal import Decimal
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
            queryset = queryset.filter(Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q) | Q(id__icontains=q))
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(is_active=True)
        products_data = {
            p.id: {
                'sale_price': float(p.sale_price),
                'cost_price': float(p.cost_price),
                'unit_type': p.unit_type
            } for p in products
        }
        context['products_json'] = json.dumps(products_data, cls=DjangoJSONEncoder)
        return context

    def form_valid(self, form):
        form.instance.seller = self.request.user
        response = super().form_valid(form)
        sale = self.object
        qty_to_subtract = sale.quantity_piece
        if qty_to_subtract and qty_to_subtract > 0 and sale.location and sale.product:
            with transaction.atomic():
                inventory, _ = Inventory.objects.get_or_create(location=sale.location, product=sale.product, defaults={'quantity': 0})
                inventory.quantity -= qty_to_subtract
                inventory.save()
                InventoryMovement.objects.create(location=sale.location, product=sale.product, quantity=qty_to_subtract, movement_type='VENTA', date=sale.day, sale=sale)
        return response

class SaleUpdateView(LoginRequiredMixin, UpdateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/sale_form.html'
    success_url = reverse_lazy('sale_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(is_active=True)
        products_data = {
            p.id: {
                'sale_price': float(p.sale_price),
                'cost_price': float(p.cost_price),
                'unit_type': p.unit_type
            } for p in products
        }
        context['products_json'] = json.dumps(products_data, cls=DjangoJSONEncoder)
        return context

    def form_valid(self, form):
        old_sale = Sale.objects.get(pk=self.object.pk)
        response = super().form_valid(form)
        new_sale = self.object
        with transaction.atomic():
            old_qty = old_sale.quantity_piece
            if old_sale.location and old_qty and old_qty > 0 and old_sale.product:
                inv_old, _ = Inventory.objects.get_or_create(location=old_sale.location, product=old_sale.product, defaults={'quantity': 0})
                inv_old.quantity += old_qty
                inv_old.save()
            new_qty = new_sale.quantity_piece
            if new_sale.location and new_qty and new_qty > 0 and new_sale.product:
                inv_new, _ = Inventory.objects.get_or_create(location=new_sale.location, product=new_sale.product, defaults={'quantity': 0})
                inv_new.quantity -= new_qty
                inv_new.save()

            # Sync inventory movement
            if new_qty and new_qty > 0 and new_sale.location and new_sale.product:
                movement, created = InventoryMovement.objects.get_or_create(
                    sale=new_sale,
                    defaults={
                        'location': new_sale.location,
                        'product': new_sale.product,
                        'quantity': new_qty,
                        'movement_type': 'VENTA',
                        'date': new_sale.day
                    }
                )
                if not created:
                    movement.location = new_sale.location
                    movement.product = new_sale.product
                    movement.quantity = new_qty
                    movement.date = new_sale.day
                    movement.save()
            else:
                InventoryMovement.objects.filter(sale=new_sale).delete()
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(is_active=True)
        products_data = {
            p.id: {
                'sale_price': float(p.sale_price),
                'cost_price': float(p.cost_price),
                'unit_type': p.unit_type
            } for p in products
        }
        context['products_json'] = json.dumps(products_data, cls=DjangoJSONEncoder)
        return context

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
        product=order.product,
        sale_type=order.sale_type,
        quantity_kg=order.quantity_kg,
        quantity_piece=order.quantity_piece,
        unit_price=order.unit_price,
        cost_price=0,
        price=order.total_price,
        amount_paid=order.total_price,
        is_paid=True,
        payment_date=timezone.now().date(),
        seller=order.seller,
        payment_method=order.payment_method
    )
    
    # Update Inventory
    qty_to_subtract = sale.quantity_piece
    if qty_to_subtract and qty_to_subtract > 0 and sale.location and sale.product:
        inventory, _ = Inventory.objects.get_or_create(location=sale.location, product=sale.product, defaults={'quantity': 0})
        inventory.quantity -= qty_to_subtract
        inventory.save()
        InventoryMovement.objects.create(location=sale.location, product=sale.product, quantity=qty_to_subtract, movement_type='VENTA', date=sale.day, sale=sale)
    
    order.status = 'COMPLETADO'
    order.save()
    
    messages.success(request, f"Pedido #{order.id} convertido en venta exitosamente.")
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('order_list')

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
            .annotate(customer_name=Concat('customer__first_name', models.Value(' '), 'customer__last_name'))\
            .values('customer_name')\
            .annotate(total=Sum('price'))\
            .order_by('-total')[:5]
            
        customer_labels = [entry['customer_name'] for entry in top_customers]
        customer_data = [float(entry['total']) for entry in top_customers]

        # 4. Sales by Seller (Selected Month)
        seller_sales = Sale.objects.filter(day__range=[month_start, month_end])\
            .values('seller__username')\
            .annotate(total=Sum('price'))\
            .order_by('seller__username')

        # 5. Expenses & Profit (Selected Month)
        total_sales_month = Sale.objects.filter(day__range=[month_start, month_end]).aggregate(Sum('price'))['price__sum'] or Decimal('0.00')
        total_expenses_month = Expense.objects.filter(date__range=[month_start, month_end]).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        supplier_cost_month = Expense.objects.filter(category='COMPRA_HUEVO', date__range=[month_start, month_end]).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        net_profit_month = total_sales_month - total_expenses_month
        
        # Calculate volume proportions: PRODUCCION vs COMPRA in the selected month
        total_prod_equiv = InventoryMovement.objects.filter(movement_type='PRODUCCION', date__range=[month_start, month_end]).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_compra_equiv = InventoryMovement.objects.filter(movement_type='COMPRA', date__range=[month_start, month_end]).aggregate(Sum('quantity'))['quantity__sum'] or 0

        total_vol = Decimal(str(total_prod_equiv)) + Decimal(str(total_compra_equiv))
        if total_vol > 0:
            own_ratio = Decimal(str(total_prod_equiv)) / total_vol
            supplier_ratio = Decimal(str(total_compra_equiv)) / total_vol
        else:
            own_ratio = Decimal('1.00')
            supplier_ratio = Decimal('0.00')

        own_sales_month = total_sales_month * own_ratio
        supplier_sales_month = total_sales_month * supplier_ratio

        context['total_sales_month'] = total_sales_month
        context['total_expenses_month'] = total_expenses_month
        context['net_profit_month'] = net_profit_month
        context['own_sales_month'] = own_sales_month
        context['supplier_sales_month'] = supplier_sales_month
        context['supplier_cost_month'] = supplier_cost_month

        # Egg production and sales for selected month
        eggs_produced_month = InventoryMovement.objects.filter(
            movement_type='PRODUCCION',
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0

        # Total sales in pieces and kg
        total_sold_pieces_month = Sale.objects.filter(day__range=[month_start, month_end]).aggregate(Sum('quantity_piece'))['quantity_piece__sum'] or 0
        total_sold_kg_month = Sale.objects.filter(day__range=[month_start, month_end]).aggregate(Sum('quantity_kg'))['quantity_kg__sum'] or Decimal('0.00')

        own_sold_pieces_month = Decimal(str(total_sold_pieces_month)) * own_ratio
        supplier_sold_pieces_month = Decimal(str(total_sold_pieces_month)) * supplier_ratio

        own_sold_kg_month = total_sold_kg_month * own_ratio
        supplier_sold_kg_month = total_sold_kg_month * supplier_ratio

        context['eggs_produced_month'] = eggs_produced_month
        context['own_sold_pieces_month'] = float(own_sold_pieces_month)
        context['supplier_sold_pieces_month'] = float(supplier_sold_pieces_month)
        context['own_sold_kg_month'] = own_sold_kg_month
        context['supplier_sold_kg_month'] = supplier_sold_kg_month
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

            s_m = Sale.objects.filter(day__range=[ms, me]).aggregate(Sum('price'))['price__sum'] or Decimal('0.00')
            e_m = Expense.objects.filter(date__range=[ms, me]).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

            # Calculate volume proportions: PRODUCCION vs COMPRA
            total_prod_equiv = InventoryMovement.objects.filter(movement_type='PRODUCCION', date__range=[ms, me]).aggregate(Sum('quantity'))['quantity__sum'] or 0
            total_compra_equiv = InventoryMovement.objects.filter(movement_type='COMPRA', date__range=[ms, me]).aggregate(Sum('quantity'))['quantity__sum'] or 0

            total_vol = Decimal(str(total_prod_equiv)) + Decimal(str(total_compra_equiv))
            if total_vol > 0:
                own_ratio = Decimal(str(total_prod_equiv)) / total_vol
                supplier_ratio = Decimal(str(total_compra_equiv)) / total_vol
            else:
                own_ratio = Decimal('1.00')
                supplier_ratio = Decimal('0.00')

            s_m_own = s_m * own_ratio
            s_m_supplier = s_m * supplier_ratio

            eggs_prod_m = InventoryMovement.objects.filter(
                movement_type='PRODUCCION',
                date__gte=ms,
                date__lte=me
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0
            eggs_sold_p_m = Sale.objects.filter(day__range=[ms, me]).aggregate(
                Sum('quantity_piece'))['quantity_piece__sum'] or 0
            eggs_sold_k_m = Sale.objects.filter(day__range=[ms, me]).aggregate(
                Sum('quantity_kg'))['quantity_kg__sum'] or Decimal('0.00')

            monthly_financial_data.append({
                'month': am['label'],
                'total_sales': s_m,
                'own_sales': s_m_own,
                'supplier_sales': s_m_supplier,
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
            # Total revenue
            s_total = Sale.objects.filter(day__range=[ms, me]).aggregate(Sum('price'))['price__sum'] or Decimal('0.00')

            # Calculate volume proportions: PRODUCCION vs COMPRA
            total_prod_equiv = InventoryMovement.objects.filter(movement_type='PRODUCCION', date__range=[ms, me]).aggregate(Sum('quantity'))['quantity__sum'] or 0
            total_compra_equiv = InventoryMovement.objects.filter(movement_type='COMPRA', date__range=[ms, me]).aggregate(Sum('quantity'))['quantity__sum'] or 0

            total_vol = Decimal(str(total_prod_equiv)) + Decimal(str(total_compra_equiv))
            if total_vol > 0:
                own_ratio = Decimal(str(total_prod_equiv)) / total_vol
                supplier_ratio = Decimal(str(total_compra_equiv)) / total_vol
            else:
                own_ratio = Decimal('1.00')
                supplier_ratio = Decimal('0.00')

            # Proportional Sales split
            s_own = s_total * own_ratio
            s_supplier = s_total * supplier_ratio

            # Costs:
            # Supplier cost is the actual logged expense for buying huevo
            c_supplier = Expense.objects.filter(category='COMPRA_HUEVO', date__range=[ms, me]).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            # Total running farm expenses (excl. supplier egg cost)
            total_exp = Expense.objects.filter(date__range=[ms, me]).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            farm_exp = total_exp - c_supplier
            
            p_own = s_own - farm_exp
            p_supplier = s_supplier - c_supplier
            p_total = p_own + p_supplier

            eggs_prod = InventoryMovement.objects.filter(
                movement_type='PRODUCCION',
                date__gte=ms,
                date__lte=me
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0

            monthly_data.append({
                'month': f"{month_names_es[ms.month]} {ms.year}",
                'sales': s_total,
                'sales_own': s_own,
                'sales_supplier': s_supplier,
                'cost_supplier': c_supplier,
                'expenses': farm_exp,
                'profit': p_total,
                'profit_own': p_own,
                'profit_supplier': p_supplier,
                'eggs_produced': eggs_prod,
            })

        # Only use months with BOTH sales and expenses for KPI averages.
        # Months missing either (e.g. no expenses registered) would skew profit/margin.
        complete_months = [m for m in monthly_data if m['sales'] > 0 and m['expenses'] > 0]
        months_of_data = len(complete_months)

        if complete_months:
            avg_monthly_sales = sum(m['sales'] for m in complete_months) / Decimal(len(complete_months))
            avg_monthly_sales_own = sum(m['sales_own'] for m in complete_months) / Decimal(len(complete_months))
            avg_monthly_sales_supplier = sum(m['sales_supplier'] for m in complete_months) / Decimal(len(complete_months))
            avg_monthly_expenses = sum(m['expenses'] for m in complete_months) / Decimal(len(complete_months))
            avg_monthly_profit = sum(m['profit'] for m in complete_months) / Decimal(len(complete_months))
            avg_monthly_profit_own = sum(m['profit_own'] for m in complete_months) / Decimal(len(complete_months))
            avg_monthly_profit_supplier = sum(m['profit_supplier'] for m in complete_months) / Decimal(len(complete_months))
            profit_margin_pct = (avg_monthly_profit / avg_monthly_sales * Decimal('100.00')) if avg_monthly_sales > 0 else Decimal('0.00')

            growth_rates = []
            for i in range(1, len(complete_months)):
                prev_s = complete_months[i - 1]['sales']
                curr_s = complete_months[i]['sales']
                if prev_s > 0:
                    growth_rates.append((curr_s - prev_s) / prev_s * Decimal('100.00'))
            avg_monthly_growth = sum(growth_rates) / Decimal(len(growth_rates)) if growth_rates else Decimal('0.00')
        else:
            avg_monthly_sales = avg_monthly_sales_own = avg_monthly_sales_supplier = avg_monthly_expenses = avg_monthly_profit = avg_monthly_profit_own = avg_monthly_profit_supplier = Decimal('0.00')
            profit_margin_pct = avg_monthly_growth = Decimal('0.00')

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
            'avg_monthly_sales_own': avg_monthly_sales_own,
            'avg_monthly_sales_supplier': avg_monthly_sales_supplier,
            'avg_monthly_expenses': avg_monthly_expenses,
            'avg_monthly_profit': avg_monthly_profit,
            'avg_monthly_profit_own': avg_monthly_profit_own,
            'avg_monthly_profit_supplier': avg_monthly_profit_supplier,
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


class RecurringOrderListView(LoginRequiredMixin, ListView):
    model = RecurringOrder
    template_name = 'sales/recurring_order_list.html'
    context_object_name = 'recurring_orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = RecurringOrder.objects.all().order_by('customer__first_name', 'customer__last_name')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(customer__first_name__icontains=q) |
                Q(customer__last_name__icontains=q) |
                Q(product__name__icontains=q)
            )
        return queryset

class RecurringOrderGenerateView(LoginRequiredMixin, ListView):
    model = RecurringOrder
    template_name = 'sales/recurring_order_generate.html'
    context_object_name = 'recurring_orders'

    def get_queryset(self):
        return RecurringOrder.objects.filter(is_active=True).order_by('customer__first_name', 'customer__last_name')

class RecurringOrderCreateView(LoginRequiredMixin, CreateView):
    model = RecurringOrder
    form_class = RecurringOrderForm
    template_name = 'sales/recurring_order_form.html'
    success_url = reverse_lazy('recurring_order_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(is_active=True)
        products_data = {
            p.id: {
                'sale_price': float(p.sale_price),
                'cost_price': float(p.cost_price),
                'unit_type': p.unit_type
            } for p in products
        }
        context['products_json'] = json.dumps(products_data, cls=DjangoJSONEncoder)
        return context

class RecurringOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = RecurringOrder
    form_class = RecurringOrderForm
    template_name = 'sales/recurring_order_form.html'
    success_url = reverse_lazy('recurring_order_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(is_active=True)
        products_data = {
            p.id: {
                'sale_price': float(p.sale_price),
                'cost_price': float(p.cost_price),
                'unit_type': p.unit_type
            } for p in products
        }
        context['products_json'] = json.dumps(products_data, cls=DjangoJSONEncoder)
        return context

from django.views.generic.edit import DeleteView
class RecurringOrderDeleteView(LoginRequiredMixin, DeleteView):
    model = RecurringOrder
    template_name = 'sales/recurring_order_confirm_delete.html'
    success_url = reverse_lazy('recurring_order_list')

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

@require_POST
@login_required
@transaction.atomic
def generate_recurring_orders_view(request):
    import datetime
    recurring_ids = request.POST.getlist('recurring_order_ids')
    delivery_date_str = request.POST.get('delivery_date')
    
    if not delivery_date_str:
        messages.error(request, "Debe seleccionar una fecha de reparto.")
        return redirect('recurring_order_generate_list')
        
    try:
        delivery_date = datetime.datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Fecha de reparto inválida.")
        return redirect('recurring_order_generate_list')
        
    if not recurring_ids:
        messages.error(request, "Debe seleccionar al menos un pedido recurrente.")
        return redirect('recurring_order_generate_list')
        
    generated_count = 0
    for ro_id in recurring_ids:
        try:
            ro = RecurringOrder.objects.get(pk=ro_id, is_active=True)
            Order.objects.create(
                customer=ro.customer,
                location=ro.location,
                product=ro.product,
                sale_type=ro.sale_type,
                quantity_kg=ro.quantity_kg,
                quantity_piece=ro.quantity_piece,
                unit_price=ro.unit_price,
                total_price=ro.total_price,
                payment_method=ro.payment_method,
                status='PENDIENTE',
                delivery_date=delivery_date,
                seller=request.user
            )
            ro.last_generated_date = timezone.now().date()
            ro.save()
            generated_count += 1
        except RecurringOrder.DoesNotExist:
            continue
            
    messages.success(request, f"Se han generado {generated_count} pedidos pendientes para el día {delivery_date.strftime('%d/%m/%Y')} exitosamente.")
    return redirect('recurring_order_generate_list')


class RouteOptimizerView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/route_optimizer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        delivery_date_str = self.request.GET.get('delivery_date')
        if delivery_date_str:
            try:
                import datetime
                delivery_date = datetime.datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
            except ValueError:
                delivery_date = timezone.now().date()
        else:
            delivery_date = timezone.now().date()

        orders = Order.objects.filter(status='PENDIENTE', delivery_date=delivery_date)
        locations = Location.objects.all()
        
        # Serialize orders for JavaScript optimization
        orders_data = []
        for o in orders:
            cust = o.customer
            orders_data.append({
                'id': o.id,
                'customer_name': cust.name,
                'address': cust.address,
                'phone': cust.phone_number,
                'lat': float(cust.latitude) if cust.latitude else None,
                'lon': float(cust.longitude) if cust.longitude else None,
                'product_name': o.product.name if o.product else "Huevo",
                'quantity': float(o.quantity_kg) if o.sale_type == 'KILO' else int(o.quantity_piece or 0),
                'unit': 'Kg' if o.sale_type == 'KILO' else 'Pzas'
            })
            
        locations_data = [
            {
                'id': loc.id,
                'name': loc.name,
                'lat': float(loc.latitude) if loc.latitude else None,
                'lon': float(loc.longitude) if loc.longitude else None,
            } for loc in locations
        ]

        context.update({
            'delivery_date': delivery_date,
            'orders': orders,
            'orders_json': json.dumps(orders_data, cls=DjangoJSONEncoder),
            'locations': locations,
            'locations_json': json.dumps(locations_data, cls=DjangoJSONEncoder)
        })
        return context

