from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from .models import *
from uuid import uuid4


#====================================== Category Admin ================================================

class CategoryFilter(SimpleListFilter):
    """
    A custom filter for narrowing down categories based on their parent category.

    This filter is designed for hierarchical category models, allowing admin users to filter
    and view only the subcategories of a selected parent category.

    Methods:
        lookups(request, model_admin):
            Returns a list of unique parent categories to populate the filter options.

        queryset(request, queryset):
            Filters the queryset to include only categories whose parent matches the selected value.
    """
    title = "Food Supplie's Categories"
    parameter_name = "Category"
    
    def lookups(self, request, model_admin):
        parent_categories = Category.objects.filter(~Q(parent=None))
        parents = set([category.parent for category in parent_categories])
        parents = Category.objects.filter(Category_parent__isnull=False).distinct()
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
    list_display = ["id", "slug", "current_stock", "category", "price", "created_at", "updated_at"]
    list_filter = ["category"]
    search_fields = ["slug"]
    ordering = ["slug"]
    
    def current_stock(self, obj):
        # return Warehouse.total_stock(product=obj)
        return obj.current_stock
    current_stock.short_description = "Current Stock" 

    
#====================================== Gallery Admin =================================================

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ["product"]
    list_filter = ["product"]
    search_fields = ["product"]
    ordering = ["product"]


#====================================== Wishlist Admin ================================================

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "product", "price"]
    search_fields = ["user", "product"]
    ordering = ["user", "id"]

    def price(self, obj):
        return obj.get_product_price()
    
    
#====================================== Warehouse Admin ===============================================

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "current_stock", "is_available", "price", "warehouse_type", "stock", "created_at", "updated_at"]
    list_filter = ["warehouse_type"]
    search_fields = ["product", "warehouse_type"]
    ordering = ["id"]
        
    def current_stock(self, obj):
        # return Warehouse.total_stock(product=obj.product)
        return obj.product.current_stock
    current_stock.short_description = "Current Stock"
    

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

        
#====================================== ShoppingCart Admin ============================================

class CartItemInLine(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ["status", "grand_total"]


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "status", "total_price"]
    search_fields = ["online_customer", "in_person_customer", "products"]
    ordering = ["id"]
    inlines = [CartItemInLine]
    readonly_fields = ["status", "total_price"]
    
    def customer(self, obj):
        return obj.customer()
    
    def get_fieldsets(self, request, obj = None):
        return [
            ("Shopping Cart", {"fields": ("in_person_customer", "online_customer", "total_price")}),
        ]
     
    # def save_related(self, request, form, formsets, change):
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
    list_display = ["id", "cart", "product", "status", "quantity", "price", "grand_total"]
    search_fields = ["id", "product", "status"]
    ordering = ["id"]
    readonly_fields = ["status", "grand_total", "price"]
    
    def price(self, obj):
        return obj.get_product_price()
    
      
#====================================== Delivery Schedule Admin =======================================

@admin.register(DeliverySchedule)
class DeliveryScheduleAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "date", "day", "time", "delivery_method", "delivery_cost"]
    list_filter = ["day", "time", "delivery_method"]
    search_fields = ["date", "day", "time"]
    ordering = ["id", "date", "time"]
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
    list_display = ["order_number", "customer", "order_type", "delivery_schedule", "payment_method", "total_amount", "amount_payable", "discount_applied", "status", "created_at", "updated_at"]
    list_filter = ["order_type", "status", "payment_method"]
    search_fields = ["order_number", "online_customer", "in_person_customer", "payment_method"]
    ordering = ["created_at"]
    exclude = ["description", "order_type"]
    readonly_fields = ["total_amount"]
    
    def customer(self, obj):
        return obj.customer()
    
    def get_fieldsets(self, request, obj = None):
        return [
            ("Order Info", {"fields": ("in_person_customer", "online_customer", "shopping_cart", "status", "delivery_schedule")}),
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
    list_display = ["id", "user", "order", "amount", "type", "is_paid", "reference_id", "created_at"]
    search_fields = ["user", "order"]
    ordering = ["order"]
    exclude = ["is_paid"]
    readonly_fields = ["amount"]
    
    def save_model(self, request, obj, form, change):
        try:
            obj.reference_id = uuid4().hex[:10].lower()
            super().save_model(request, obj, form, change)
        except ValidationError as error:
            self.message_user(request, f"Error: {error}", level="error")
    
    class Media:
        js = (
            "https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js",
            "js/admin_transaction.js",
        )
        
        
#====================================== Delivery Admin ================================================

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "tracking_id", "status", "shipped_at", "delivered_at"]
    search_fields = ["tracking_id"]
    ordering = ["order"]
    exclude = ["status"]
    
    
#====================================== Refund Admin ==================================================

@admin.register(Refund)
class RefundAddmin(admin.ModelAdmin):
    list_display = ["user", "order", "amount", "method", "status", "created_at", "processed_at"]
    search_fields = ["order"]
    ordering = ["order"]


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