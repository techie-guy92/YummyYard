from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from .models import *


#===================================== Actions ========================================================


#====================================== Category Admin ================================================

class CategoryFilter(SimpleListFilter):
    title = "Food Supplie's Categories"
    parameter_name = "Category"
    
    def lookups(self, request, model_admin):
        parent_categories = Category.objects.filter(~Q(parent=None))
        parents = set([category.parent for category in parent_categories])
        return [(obj.id, obj.name) for obj in parents]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(parent=self.value())
        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "parent", "slug", "created_at", "updated_at"]
    list_filter = [CategoryFilter]
    search_fields = ["slug", "parent"]
    ordering = ["id"]
    
    
#====================================== Product Admin =================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "slug", "total_stock", "category", "price", "created_at", "updated_at"]
    search_fields = ["slug"]
    ordering = ["slug"]
    
    def total_stock(self, obj):
        return Warehouse.total_stock(product=obj)
    total_stock.short_description = "Total Stock"  

    
#====================================== Gallery Admin =================================================

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ["product"]
    list_filter = ["product"]
    search_fields = ["product"]
    ordering = ["product"]

    
#====================================== Warehouse Admin ===============================================

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "price", "warehouse_type", "stock", "is_available", "total_stock", "created_at", "updated_at"]
    list_filter = ["warehouse_type"]
    search_fields = ["product", "warehouse_type"]
    ordering = ["id"]
    
    def total_stock(self, obj):
        return Warehouse.total_stock(product=obj.product)
    total_stock.short_description = "Total Stock"
    

#====================================== Coupon Admin ==================================================

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["id", "code", "get_category_display", "discount_percentage", "max_usage", "usage_count", "is_active", "valid_from", "valid_to"]
    list_filter = ["is_active"]
    search_fields = ["valid_from", "valid_to"]
    ordering = ["is_active", "valid_to", "discount_percentage"]
    list_editable = ["is_active"]

    def get_category_display(self, obj):
        return obj.category.name if obj.category else "All"
    get_category_display.short_description = "Category"
    
    # Second Approch
    # def save_model(self, request, obj, form, change):
    #     if not obj.category:
    #         all_category, created = Category.objects.get_or_create(name="All", defaults={"slug": "all"})
    #         obj.category = all_category
    #     super().save_model(request, obj, form, change)


#====================================== Wishlist Admin ================================================

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "product", "price"]
    search_fields = ["user", "product"]
    ordering = ["user", "id"]

    def price(self, obj):
        return obj.get_product_price()

        
#====================================== ShoppingCart Admin ============================================

class CartItemInLine(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ["grand_total"]


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "total_price"]
    search_fields = ["online_customer", "in_person_customer", "products"]
    ordering = ["id"]
    inlines = [CartItemInLine]
    readonly_fields = ["total_price"]
    
    def customer(self, obj):
        return obj.customer()
    
    def get_fieldsets(self, request, obj = None):
        return [
            ("Shopping Cart", {"fields": ("in_person_customer", "online_customer", "total_price")}),
        ]
     
    # def save_related(self, request, form, formsets, change):
    #     # Save inline items first
    #     super().save_related(request, form, formsets, change)
    #     # Recalculate total_price after all related items (CartItems) are saved
    #     obj = form.instance
    #     obj.total_price = obj.calculate_total_price()
    #     obj.save(update_fields=["total_price"])
    
    class Media:
        js = (
            "https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js",
            "js/admin_shoppingCarts.js",
        )
    
    
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "cart", "product", "quantity", "price", "grand_total"]
    search_fields = ["id", "product"]
    ordering = ["id"]
    readonly_fields = ["grand_total", "price"]
    
    def price(self, obj):
        return obj.get_product_price()
    
    
#====================================== Delivery Schedule Admin =======================================

@admin.register(DeliverySchedule)
class DeliveryScheduleAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "date", "day", "time", "delivery_method", "delivery_cost"]
    list_filter = ["day", "time", "delivery_method"]
    search_fields = ["date", "day", "time"]
    ordering = ["date", "time"]
    readonly_fields = ["delivery_cost"]

    def customer(self, obj):
        return obj.customer()
    
    # def save_model(self, request, obj, form, change):
    #     try:
    #         obj.reserve_delivery_slot()
    #         super().save_model(request, obj, form, change)
    #     except ValidationError as error:
    #         self.message_user(request, f"Error: {error}", level="error")

    class Media:
        js = (
            "https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js",
            "js/admin_deliverySchedule.js",
        )
        
        
#====================================== Order Admin ===================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "order_type", "payment_method", "total_amount", "amount_payable", "discount_applied", "delivery_schedule", "status", "created_at", "updated_at"]
    list_filter = ["order_type", "status", "payment_method"]
    search_fields = ["online_customer", "in_person_customer", "payment_method"]
    ordering = ["created_at"]
    exclude = ["order_type", "status", "description"]
    
    def customer(self, obj):
        return obj.customer()
    
    def get_fieldsets(self, request, obj = None):
        return [
            ("Order Info", {"fields": ("in_person_customer", "online_customer", "shopping_cart", "delivery_schedule")}),
            ("Order Payment", {"fields": ("payment_method", "total_amount")}),
        ]
    
    class Media:
        js = (
            "https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js",
            "js/admin_orders.js",
        )
        
        
#====================================== Transaction Admin =============================================

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "order", "amount", "is_successful", "payment_id", "created_at"]
    search_fields = ["user", "order"]
    ordering = ["order"]


#====================================== Delivery Admin ================================================

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "tracking_id", "status", "shipped_at", "delivered_at"]
    search_fields = ["tracking_id"]
    ordering = ["order"]
    exclude = ["status"]


#====================================== UserView Admin ================================================

@admin.register(UserView)
class UserViewAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "view_count", "last_seen"]
    search_fields = ["product"]
    ordering = ["product", "view_count", "last_seen"]


#====================================== Rating Admin ==================================================

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "rating", "review", "created_at"]
    list_filter = ["rating"]
    search_fields = ["product", "rating"]
    ordering = ["product", "rating"]


#====================================== Notification Admin ============================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    pass


#======================================================================================================