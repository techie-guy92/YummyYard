from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from .models import CustomUser

@staff_member_required
def print_customers_view(request):
    customers = CustomUser.objects.all() 
    return render(request, "admin/print_customers.html", {"customers": customers})
