from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseForbidden
from django.urls import path
from .forms import CustomUserForm
from .models import *
from .admin_views import print_customers_view


#==================================== Custom User Admin =========================================

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserForm
    
    list_display = ("id", "username", "first_name", "last_name", "email", "user_type", "is_active", "is_premium", "is_admin", "is_superuser", "joined_at", "updated_at",)
    list_filter = ("user_type", "is_active", "is_premium", "is_admin", "is_superuser",)
    list_search = ("username",)
    list_editable = ()
    ordering = ("id",)
    # change_list_template = "admin/customuser_change_list.html"
    
    def get_list_display(self, request):
        if request.user.is_superuser:
            self.list_editable = ("is_active", "is_premium", "is_admin",)
        else:
            self.list_editable = ("is_active", "is_premium",)
        return super().get_list_display(request)
    
    add_fieldsets = (
        ("Personal Info", {"fields": ("first_name", "last_name", "email",)}),
        ("Authentication", {"fields": ("username", "password", "re_password",)}),
    )
    
    fieldsets = (
        ("Personal Info", {"fields": ("first_name", "last_name", "email",)}),
        ("Authentication", {"fields": ("username", "password",)}),
    )
    
    def get_add_fieldsets(self, request, obj = None):
        add_fieldsets = list(self.add_fieldsets)
        if request.user.is_superuser:
            add_fieldsets += (
                ("Status", {"fields": ("user_type", "is_active", "is_admin", "is_superuser",)}),
                ("Permissions", {"fields": ("user_permissions", "groups",)}),
            )
        elif request.user.is_admin:
            add_fieldsets.append(("Status", {"fields": ("user_type", "is_active",)}),) 
        return add_fieldsets
    
    def get_fieldsets(self, request, obj = None):
        fieldsets = list(super().get_fieldsets(request, obj))
        if request.user.is_superuser:
            fieldsets += (
                ("Status", {"fields": ("user_type", "is_active", "is_admin", "is_superuser",)}),
                ("Permissions", {"fields": ("user_permissions", "groups",)}),
            )
        elif request.user.is_admin:
            fieldsets.append(("Status", {"fields": ("user_type", "is_active",)}))
        return fieldsets
    
    filter_horizontal = ("user_permissions", "groups",)
    
    def has_delete_permission(self, request, obj = None):
        if obj and not request.user.is_superuser:
            return obj.id == request.user.id
        return super().has_delete_permission(request, obj)
    
    def change_view(self, request, object_id, form_url = "", extra_context = None):
        user = CustomUser.objects.get(pk=object_id)
        if user != request.user and not request.user.is_superuser and user.is_admin:
            return HttpResponseForbidden('<h1 style="color:red; text-align:center; margin-top:100px"> شما اجازه مشاهده کردن صفحه دیگر ادمین ها را ندارید </h1>')
        if user != request.user and user.is_superuser:
            return HttpResponseForbidden('<h1 style="color:black; text-align:center; margin-top:100px"> شما اجازه مشاهده کردن صفحه دیگر ابر کاربر ها را ندارید </h1>')
        return super().change_view(request, object_id, form_url, extra_context)
    
    # def get_urls(self):
    #     urls = super().get_urls()
    #     custom_urls = [path("print-customers/", self.admin_site.admin_view(print_customers_view), name="print_customers"),]
    #     return custom_urls + urls
    
    class Media:
        js = (
            "https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js",
            "js/admin_userInfo.js",
        )        

admin.site.register(CustomUser, CustomUserAdmin)


#==================================== User Profile Admin ========================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "gender",)
    list_filter = ("gender",)
    list_search = ("user", "phone",)
    ordering = ("user",)
    
    
#====================================== InPersonCustomer Model ========================================

@admin.register(InPersonCustomer)
class InPersonCustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "last_name", "first_name", "phone",)
    ordering = ("last_name", "first_name",)
    search_fields = ("phone",)


#==================================== Premium Subscription Admin ================================

@admin.register(PremiumSubscription)
class PremiumSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "start_date", "expiry_date",)
    list_search = ("user",)
    ordering = ("user",)
    
    
#==================================== Payment Admin =============================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "user", "is_sucessful", "payment_date",)
    list_search = ("payment_id",)
    ordering = ("payment_id",)
    
    
#================================================================================================