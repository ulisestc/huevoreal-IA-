from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class SellerCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'VENDEDOR'
        if commit:
            user.save()
        return user
