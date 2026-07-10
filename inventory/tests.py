from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Supplier

class InventoryTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')
        
    def test_product_list_view(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)

    def test_supplier_list_view(self):
        response = self.client.get(reverse('supplier_list'))
        self.assertEqual(response.status_code, 200)
