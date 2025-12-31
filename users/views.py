from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import SellerCreationForm

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')

@user_passes_test(is_admin)
def register_seller(request):
    if request.method == 'POST':
        form = SellerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = SellerCreationForm()
    return render(request, 'users/register_seller.html', {'form': form})

def login_redirect(request):
    return redirect('login')