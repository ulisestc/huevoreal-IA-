from django.test import TestCase
from django.contrib.auth import get_user_model
from inventory.models import Supplier, Product, Location
from customers.models import Customer
from sales.models import Sale, Order, RecurringOrder
from django.utils import timezone
import datetime

class SalesTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='password')
        
        self.supplier = Supplier.objects.create(
            name="Socio Huevo",
            phone="12345"
        )
        
        self.product_piece = Product.objects.create(
            name="Huevo Orgánico",
            category="HUEVO",
            supplier=self.supplier,
            unit_type="PIEZA",
            cost_price=1.00,
            sale_price=1.50
        )
        
        self.product_kg = Product.objects.create(
            name="Huevo Orgánico (Granel)",
            category="HUEVO",
            supplier=self.supplier,
            unit_type="KILO",
            cost_price=80.00,
            sale_price=120.00
        )

        self.customer = Customer.objects.create(
            first_name="Juan",
            last_name="Perez",
            address="Calle 123",
            phone_number="555-555"
        )
        
        self.location = Location.objects.create(
            name="Bodega Central"
        )

    def test_profit_calculations(self):
        # Sale for piece-based product
        sale1 = Sale.objects.create(
            day=timezone.now().date(),
            location=self.location,
            product=self.product_piece,
            customer=self.customer,
            sale_type='PIEZA',
            quantity_piece=10,
            unit_price=1.50,
            cost_price=1.00,
            price=15.00,
            amount_paid=15.00,
            is_paid=True,
            payment_date=timezone.now().date(),
            payment_method='EFECTIVO',
            seller=self.user
        )
        
        # Total profit should be (1.50 - 1.00) * 10 = 5.00
        qty = sale1.quantity_piece
        cost = float(qty) * float(sale1.cost_price)
        revenue = float(sale1.price)
        profit = revenue - cost
        self.assertEqual(profit, 5.00)

    def test_recurring_order_model(self):
        ro = RecurringOrder.objects.create(
            customer=self.customer,
            product=self.product_piece,
            location=self.location,
            sale_type='PIEZA',
            quantity_piece=15,
            unit_price=1.50,
            total_price=22.50,
            payment_method='EFECTIVO',
            frequency='SEMANAL',
            day_of_week='2',
            is_active=True
        )
        self.assertTrue(ro.is_active)
        self.assertEqual(ro.quantity_piece, 15)
        self.assertEqual(ro.frequency, 'SEMANAL')
        self.assertEqual(ro.day_of_week, '2')
        self.assertEqual(ro.location, self.location)

    def test_order_completion_with_inventory_kilo(self):
        from inventory.models import Inventory
        # Create initial inventory for KILO product
        inv = Inventory.objects.create(
            location=self.location,
            product=self.product_kg,
            quantity=200
        )
        
        # Create order for KILO product
        order = Order.objects.create(
            customer=self.customer,
            location=self.location,
            product=self.product_kg,
            sale_type='KILO',
            quantity_kg=10.00,
            quantity_piece=160,
            unit_price=120.00,
            total_price=1200.00,
            payment_method='EFECTIVO',
            status='PENDIENTE',
            delivery_date=timezone.now().date(),
            seller=self.user
        )
        
        # Simulate completing the order using Client
        self.client.login(username='testuser', password='password')
        self.client.post(f'/sales/orders/{order.pk}/complete/')
        
        # Refresh from DB and check status
        order.refresh_from_db()
        self.assertEqual(order.status, 'COMPLETADO')
        
        # Check inventory is subtracted correctly by 10.00 kg (10 * 16 = 160 pieces)
        inv.refresh_from_db()
        self.assertEqual(inv.quantity, 40)

    def test_order_cancellation(self):
        order = Order.objects.create(
            customer=self.customer,
            location=self.location,
            product=self.product_piece,
            sale_type='PIEZA',
            quantity_piece=10,
            unit_price=10.00,
            total_price=100.00,
            payment_method='EFECTIVO',
            status='PENDIENTE',
            delivery_date=timezone.now().date(),
            seller=self.user
        )
        
        self.client.login(username='testuser', password='password')
        self.client.post(f'/sales/orders/{order.pk}/cancel/')
        
        order.refresh_from_db()
        self.assertEqual(order.status, 'CANCELADO')

    def test_recurring_order_views(self):
        ro = RecurringOrder.objects.create(
            customer=self.customer,
            product=self.product_piece,
            location=self.location,
            sale_type='PIEZA',
            quantity_piece=15,
            unit_price=1.50,
            total_price=22.50,
            payment_method='EFECTIVO',
            frequency='SEMANAL',
            day_of_week='2',
            is_active=True
        )
        self.client.login(username='testuser', password='password')
        
        # Test GET create
        response = self.client.get('/sales/recurring/create/')
        self.assertEqual(response.status_code, 200)

        # Test POST create
        response = self.client.post('/sales/recurring/create/', {
            'customer': self.customer.pk,
            'location': self.location.pk,
            'product': self.product_piece.pk,
            'sale_type': 'PIEZA',
            'quantity_piece': 10,
            'unit_price': 1.50,
            'total_price': 15.00,
            'payment_method': 'EFECTIVO',
            'frequency': 'SEMANAL',
            'day_of_week': '0,3',
            'is_active': True
        })
        self.assertEqual(response.status_code, 302) # Redirects to list on success

        # Test GET edit
        response = self.client.get(f'/sales/recurring/{ro.pk}/edit/')
        self.assertEqual(response.status_code, 200)

        # Test POST edit
        response = self.client.post(f'/sales/recurring/{ro.pk}/edit/', {
            'customer': self.customer.pk,
            'location': self.location.pk,
            'product': self.product_piece.pk,
            'sale_type': 'PIEZA',
            'quantity_piece': 20,
            'unit_price': 1.50,
            'total_price': 30.00,
            'payment_method': 'EFECTIVO',
            'frequency': 'QUINCENAL',
            'day_of_week': '1,4',
            'is_active': True
        })
        self.assertEqual(response.status_code, 302)

