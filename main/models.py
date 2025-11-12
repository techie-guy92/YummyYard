from django.db import models, transaction
from django.db.models import Sum, Count
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now, localtime
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.conf import settings
from logging import getLogger
from uuid import uuid4
from utilities.utilities import code_generator
from utilities.media_utils import upload_to, Arvan_storage
from users.models import InPersonCustomer, Wallet


logger = getLogger(__name__)

#====================================== Category Model ================================================

class Category(models.Model):
    """
    Represents a hierarchical product category in the system.

    Methods:
        validate_parent(): Ensures a category cannot be its own parent.
        get_all_children(): Recursively retrieves all subcategories of the current category.
        save(): Automatically validates data and generates a unique slug for the category before saving.
    """
    name = models.CharField(max_length=100, verbose_name="Category")
    parent = models.ForeignKey("Category", on_delete=models.CASCADE, related_name="Category_parent", null=True, blank=True, verbose_name="Parent")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    image = models.ImageField(upload_to=upload_to, storage=Arvan_storage, null=True, blank=True, verbose_name="Image")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.name}"
    
    def clean(self):
        self.validate_parent()
          
    def validate_parent(self):
        if self.parent and self.parent.id == self.id:
            raise ValidationError("دسته نمی‌تواند والد خودش باشد.")
        
    def get_all_children(self):
        children = []
        for child in self.Category_parent.all():
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            unique_slug = base_slug
            num = 1
            while Category.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [models.Index(fields=["name"]), models.Index(fields=["parent"])]


#====================================== Product Model =================================================

class Product(models.Model):
    """
    Represents a product available for sale in the marketplace.

    Methods:
        save(): Generates a unique slug for the product based on its name to ensure URL uniqueness.
    """
    name = models.CharField(max_length=250, verbose_name="Product") 
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="Product_category", verbose_name="Category")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    price = models.PositiveIntegerField(default=0, verbose_name="Price")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    image = models.ImageField(upload_to=upload_to, storage=Arvan_storage, null=True, blank=True, verbose_name="Image")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    @cached_property
    def current_stock(self):
        return Warehouse.total_stock(product=self)
    
    def get_cached_stock(self):
        cache_key = f"product_{self.id}_stock"
        return cache.get_or_set(cache_key, lambda: Warehouse.total_stock(product=self), settings.CACHE_TTL)
    
    def __str__(self):
        return f"{self.name}"
        
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            unique_slug = base_slug
            num = 1
            while Product.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [models.Index(fields=["name"]), models.Index(fields=["price"])]
        
        
#====================================== Gallery Model =================================================

class Gallery(models.Model):
    """
    Represents additional images for a product.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="Gallery_product", verbose_name="Product")
    image = models.ImageField(upload_to=upload_to, storage=Arvan_storage, verbose_name="Image")
    
    def __str__(self):
        return f"{self.product}"
    
    class Meta:
        verbose_name = "Gallery"
        verbose_name_plural = "Galleries"


#====================================== Wishlist Model ================================================

class Wishlist(models.Model):
    """
    Represents a user's wishlist, allowing users to save favorite products for future reference.

    Methods:
        get_product_price(): Returns the price of the product in the wishlist.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Wishlist_user", verbose_name="User")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="Wishlist_product", verbose_name="Product")
    
    def get_product_price(self):
        return self.product.price
    
    def __str__(self):
        return f"Wishlist of {self.user.username}"

    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"
        indexes = [models.Index(fields=["product"])]
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_wishlist_item")]
        
        
#====================================== Warehouse Model ===============================================

class Warehouse(models.Model):
    """
    Represents the inventory management system for a product within different warehouse operations.

    Attributes:
        product: The associated product in the warehouse.
        warehouse_type: The type of warehouse operation (e.g., input, output, defective, sent back).
        stock: The quantity of the product stored in the warehouse.
        is_available: Indicates whether the product is available in stock.
        price: The cost price of the product for company.
        created_at: The timestamp when the warehouse entry was initially recorded.
        updated_at: The timestamp when the warehouse entry was last modified.

    Methods:
        total_stock(product): Calculates the total stock for a given product by aggregating input, output, and defective stock levels.
    """
    WAREHOUSE_TYPE = [("input", "ورودی"), ("output", "خروجی"), ("defective", "مرجوعی"), ("sent_back", "مرجوع-شده")]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="Warehouse_product", verbose_name="Product")
    warehouse_type = models.CharField(max_length=10, choices=WAREHOUSE_TYPE, default="input", verbose_name="Warehouse Type")
    stock = models.PositiveIntegerField(default=0, verbose_name="Quantity")  
    is_available = models.BooleanField(default=True, editable=False, verbose_name="Is Available") 
    price = models.IntegerField(default=0, verbose_name="Cost/Sell Price")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    @staticmethod
    def total_stock(product):
        input_stock = Warehouse.objects.filter(product=product, warehouse_type="input").aggregate(total=Sum("stock"))["total"] or 0
        output_stock = Warehouse.objects.filter(product=product, warehouse_type="output").aggregate(total=Sum("stock"))["total"] or 0
        defective_stock = Warehouse.objects.filter(product=product, warehouse_type="defective").aggregate(total=Sum("stock"))["total"] or 0
        total = input_stock - (output_stock + defective_stock)
        return total
    
    def __str__(self):
        return f"{self.product} - {self.total_stock(product=self.product)}"
        
    class Meta:
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"
        indexes = [models.Index(fields=["product"]), models.Index(fields=["warehouse_type"]), models.Index(fields=["stock"]), models.Index(fields=["created_at"])]
        
        
#====================================== Coupon Model ==================================================

class Coupon(models.Model):
    """
    Represents a discount coupon that can be applied to purchases.

    Attributes:
        code: A unique identifier for the coupon which generates automatically via save() method if it is not filled.
        category: The category associated with the coupon (optional) in case a discount is going to apply for a specific category.
        discount_percentage: The percentage discount applied when using the coupon.
        max_usage: The maximum number of times the coupon can be used.
        usage_count: The number of times the coupon has been used.
        valid_from: The date and time when the coupon becomes active.
        valid_to: The date and time when the coupon expires.
        is_active: Indicates whether the coupon is currently available for use.

    Methods:
        is_expired(): Checks if the coupon has passed its expiration date.
        is_valid(): Determines if the coupon is still usable based on its active status, expiration date, and usage limit.
        save(): Automatically generates a coupon code if not provided before saving the instance.
    """
    code = models.CharField(max_length=10, blank=True, verbose_name="Code")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="Coupon_category", null=True, blank=True, verbose_name="Category")
    discount_percentage = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(10), MaxValueValidator(50)], verbose_name="Discount Percentage")
    max_usage = models.PositiveIntegerField(default=1, verbose_name="Maximum Usage")
    usage_count = models.PositiveIntegerField(default=0, editable=False, verbose_name="Usage Count")
    valid_from = models.DateTimeField(verbose_name="Valid From")
    valid_to = models.DateTimeField(verbose_name="Valid To")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    
    def is_expired(self):
        return self.valid_to < localtime(now())
    
    def is_valid(self): 
        return self.is_active and not self.is_expired() and self.usage_count <= self.max_usage
    
    def __str__(self):
        return f"{self.code}"
        
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = code_generator(5)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        indexes = [models.Index(fields=["is_active"]), models.Index(fields=["max_usage"]), models.Index(fields=["usage_count"]), models.Index(fields=["valid_from"]), models.Index(fields=["valid_to"]),]
        

#====================================== ShoppingCart Model ============================================

class ShoppingCart(models.Model):
    """
    Represents a user's shopping cart, tracking selected products and total cost during a shopping session.

    Attributes:
        online_customer (optional): The registered user who owns the shopping cart.
        in_person_customer (optional): The guest or in-person customer associated with the cart.
        products (ManyToManyField): The products added to the shopping cart, linked through `CartItem`.
        total_price: The aggregated price of all items in the shopping cart.
        status: The current status of the order (e.g., active, processed, abandoned).

    Methods:
        customer(): Returns the associated customer (either online or in-person).
        validate_customer(): Ensures a shopping cart has either an online or in-person customer (but not both).
        calculate_total_price(): Computes the total price based on items in the cart.
        place_order(): Converts the cart items into a warehouse stock record when an order is placed.
        clear_cart(): Removes all items from the cart and resets the total price.
        save(): Validates data and ensures the total price is updated after modifications.
    """
    STATUS_TYPES = [("active", "فعال"), ("processed", "پردازش-شده"), ("abandoned", "لغو-شده")]
    
    online_customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="ShoppingCart_online_customers", verbose_name="Online Customer")
    in_person_customer = models.ForeignKey(InPersonCustomer, on_delete=models.CASCADE, blank=True, null=True, related_name="ShoppingCart_in_person_customers", verbose_name="In-Person Customer")
    products = models.ManyToManyField(Product, through="CartItem", related_name="ShoppingCart_products", verbose_name="Products")
    total_price = models.PositiveIntegerField(default=0, verbose_name="Total Price")
    status = models.CharField(max_length=10, choices=STATUS_TYPES, default="active", verbose_name="Cart Status")
    
    def calculate_total_price(self):
        return sum(item.grand_total for item in CartItem.objects.filter(cart=self))
    
    def customer(self):
        return self.online_customer if self.online_customer else self.in_person_customer
    
    def place_order(self):
        with transaction.atomic():
            for item in CartItem.objects.filter(cart=self):
                Warehouse.objects.create(
                    product=item.product,
                    warehouse_type="output",
                    stock=item.quantity,
                    price=item.product.price
                )
    
    def mark_as_processed(self):
        self.status = "processed"
        self.save(update_fields=["status"])
        
    def clear_cart(self):
        cart_items = CartItem.objects.filter(cart=self, status="active")
        if self.status == "processed":
            return  
        if cart_items.exists():
            with transaction.atomic():
                self.mark_as_processed()
                cart_items.update(status="processed")
                
    def __str__(self):
        return f"{self.id} - {self.online_customer.username if self.online_customer else self.in_person_customer.first_name+' '+self.in_person_customer.last_name}"

    def clean(self):
        self.validate_customer()
        
    def validate_customer(self):
        if not self.online_customer and not self.in_person_customer:
            raise ValidationError("سبد خرید حتما باید دارای کابر آنلاین یا کاربر حضوری باشد.")
        if self.online_customer and self.in_person_customer:
            raise ValidationError("سبد خرید نمیتواند هم کاربر آنلاین داشته باشد و هم کاربر حضوری.")

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None  
        super().save(*args, **kwargs)
        if not is_new: 
            self.total_price = self.calculate_total_price()
            super().save(update_fields=["total_price"])

    class Meta:
        verbose_name = "Shopping Cart"
        verbose_name_plural = "Shopping Carts"
        indexes = [
            models.Index(fields=["online_customer"]),
            models.Index(fields=["in_person_customer"]),
            models.Index(fields=["status"]), 
        ]
        
        
class CartItem(models.Model):
    """
    Represents an individual product entry in a shopping cart.

    Attributes:
        cart: The shopping cart that contains this item.
        product: The specific product added to the cart.
        quantity: The number of units of the product selected by the customer.
        grand_total: The total cost of the product in the cart based on quantity.
        status: The current status of the order (e.g., active, processed).

    Methods:
        get_product_price(): Returns the price of the associated product.
        validate_quantity(): Ensures the quantity is greater than zero.
        validate_stock(): Confirms the requested quantity does not exceed available stock.
        validate_grand_total(): Updates the `grand_total` field based on the product price and quantity.
        save(): Ensures data integrity before storing the item in the cart.
    """
    STATUS_TYPES = [("active", "فعال"), ("processed", "پردازش-شده"), ("abandoned", "لغو-شده")]
    
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name="CartItem_cart", verbose_name="Cart")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="CartItem_product", verbose_name="Product")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    grand_total = models.PositiveIntegerField(default=0, verbose_name="Grand Total")
    status = models.CharField(max_length=10, choices=STATUS_TYPES, default="active", verbose_name="Status")
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart.online_customer.username if self.cart.online_customer else self.cart.in_person_customer.first_name+' '+self.cart.in_person_customer.last_name}'s Cart"
    
    def get_product_price(self):
        return self.product.price
    
    def clean(self):
        self.validate_quantity()
        self.validate_grand_total()
        self.validate_stock()
    
    def validate_quantity(self):
        if self.quantity <= 0:
            raise ValidationError("تعداد باید بیشتر از صفر باشد.")
    
    def validate_stock(self):
        total_stock = Warehouse.total_stock(product=self.product)
        if self.quantity > total_stock:
            raise ValidationError(f"موجودی ناکافی برای {self.product.name}. تعداد درخواستی: {self.quantity}, موجودی: {total_stock}")

    def validate_grand_total(self):
        self.grand_total = self.get_product_price() * self.quantity
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        indexes = [models.Index(fields=["cart"]), models.Index(fields=["product"])]


#====================================== Delivery Schedule Model =======================================

class DeliverySchedule(models.Model):
    """
    Represents a scheduled delivery slot for customer orders.
    This model manages delivery availability by defining valid days, time slots, capacity limits, and scheduling constraints.

    Attributes:
        user: The customer requesting the delivery.
        shopping_cart: The associated shopping cart for the delivery.
        delivery_method: The chosen delivery method (e.g., normal, fast, postal).
        date: The specific date when the delivery is scheduled.
        day: The day of the week for the delivery slot.
        time: The selected delivery timeframe (e.g., 8 - 10).
        delivery_cost: The calculated delivery cost based on the selected method.
        created_at: The timestamp when the delivery schedule was created.
        updated_at: The timestamp when the delivery schedule was last modified.

    Methods:
        customer(): Returns the username of the customer associated with the delivery.
        validate_order(): Ensures the user and associated shopping cart data are consistent.
        validate_timeframe(): Prevents scheduling deliveries in the past or beyond allowed limits.
        validate_delivery_slot(): Enforces capacity restrictions for different delivery methods.
        calculate_delivery_cost(): Determines the delivery fee based on the method selected.
        save(): Cleans, formats, and updates the delivery schedule before saving it. 
    """
    TIMES = [("8_10", "8 - 10"), ("10_12", "10 - 12"), ("12_14", "12 - 14"), ("14_16", "14 - 16"), ("16_18", "16 - 18"), ("18_20", "18 - 20"), ("20_22", "20 - 22")]
    DELIVERY_TYPES = [("normal", "ارسال-عادی"), ("fast", "ارسال-سریع"), ("postal", "پست")]
    MAX_DAYS_AHEAD = 7
    MAX_CAPACITY_DELIVERY_NORMAL = 5
    MAX_CAPACITY_DELIVERY_FAST = 3  
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="DeliverySchedule_user", verbose_name="User")
    shopping_cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name="DeliverySchedule_shopping_cart", verbose_name="Shopping Cart")
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_TYPES, verbose_name="Delivery Method")
    date = models.DateField(verbose_name="Delivery Date")
    day = models.CharField(max_length=10, verbose_name="Day of the Week")
    time = models.CharField(max_length=10, choices=TIMES, verbose_name="Time")
    delivery_cost = models.PositiveIntegerField(default=0, verbose_name="Delivery Cost")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.id} - {self.date} ({self.day}) {self.time}"

    def customer(self):
        return self.user.username
    
    def clean(self):
        self.validate_order()
        self.validate_timeframe()
        self.validate_delivery_slot()
        
    def validate_order(self):
        try:
            if not self.user:
                raise ValidationError("انتخاب کاربر ضرروری است.")
            if self.user and self.shopping_cart and self.user != self.shopping_cart.online_customer:
                raise ValidationError("کاربر و سبد خرید باید یکی باشند.")
        except Exception as error:
            raise ValidationError(f"An error occurred while validating the order: {str(error)}")
    
    def validate_timeframe(self):
        if self.time not in dict(self.TIMES):
            raise ValidationError({"time": "زمان انتخاب شده در لیست بازه‌های مجاز نیست، لطفا زمان معتبری وارد کنید."})
        crr_datetime = localtime(now())
        crr_date = crr_datetime.date()
        crr_hour = crr_datetime.hour
        if self.date < crr_date:
            raise ValidationError(f"بازه انتخابی نمیتواند در گذشته باشد و باید از امروز تا {self.MAX_DAYS_AHEAD} روز آینده باشد.")
        if (self.date - crr_date).days > self.MAX_DAYS_AHEAD:
            raise ValidationError(f"بازه زمانی انتخابی باید تا {self.MAX_DAYS_AHEAD} روز آینده باشد.")
        if self.date == crr_date:
            start_hour = int(self.time.split("_")[0])
            if start_hour <= crr_hour + 4:
                raise ValidationError(f"بازه انتخابی ({self.time}) موجود نیست. بازه انتخابی از شروع میشود {crr_hour + 4}:00. در صورت عدم وجود بازه زمانی دلخواه در امروز بازه دلخواه را برای روزهای آتی انتخاب کنید.")
                
    def validate_delivery_slot(self):
        if self.delivery_method == "fast":
            total_booked_fast = DeliverySchedule.objects.filter(date=self.date, time=self.time, delivery_method="fast").count()
            if total_booked_fast >= self.MAX_CAPACITY_DELIVERY_FAST:
                raise ValidationError("ارسال سریع برای این بازه زمانی تکمیل است. لطفا بازه های دیگر را برسی بفرمایید.")
        elif self.delivery_method == "normal":
            total_booked_normal = DeliverySchedule.objects.filter(date=self.date, time=self.time, delivery_method="normal").count()
            if total_booked_normal >= self.MAX_CAPACITY_DELIVERY_NORMAL:
                raise ValidationError("ارسال عادی برای این بازه زمانی تکمیل است. لطفا بازه های دیگر را برسی بفرمایید.")
    
    # def validate_delivery_slot(self):
    #     total_booked = (DeliverySchedule.objects.filter(date=self.date, time=self.time).values("delivery_method").annotate(delivery_count=Count("delivery_method")))
    #     total_booked_dict = {entry["delivery_method"]: entry["delivery_count"] for entry in total_booked}
    #     if total_booked_dict.get("fast", 0) >= self.MAX_CAPACITY_DELIVERY_FAST:
    #         raise ValidationError("Fast delivery slot is fully booked for this timeframe. Please select other timeframes.")
    #     if total_booked_dict.get("normal", 0) >= self.MAX_CAPACITY_DELIVERY_NORMAL:
    #         raise ValidationError("Normal delivery slot is fully booked for this timeframe. Please select other timeframes.")
        
    def calculate_delivery_cost(self):
        if self.delivery_method == "fast":
            return 50000
        elif self.delivery_method == "normal":
            return 35000
        return 20000
    
    def save(self, *args, **kwargs):
        self.full_clean()
        self.day = self.date.strftime("%A").lower()
        self.delivery_cost = self.calculate_delivery_cost()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Delivery Schedule"
        verbose_name_plural = "Delivery Schedules"
        indexes = [models.Index(fields=["date"]), models.Index(fields=["day"]), models.Index(fields=["time"])]


#====================================== Order Model ===================================================

class Order(models.Model):
    """
    Represents a final check and complete process of purchase before checkout.

    Attributes:
        online_customer (optional): The online user who placed the order.
        in_person_customer (optional): The in-person customer making a direct purchase.
        order_type: Specifies whether the order is placed online or in-person.
        shopping_cart: The linked shopping cart containing purchased items.
        delivery_schedule: The scheduled delivery details.
        payment_method: The payment method used (cash, credit card, or online).
        total_amount: The total cost before any discounts are applied.
        amount_payable: The final payable amount after applying discounts.
        discount_applied: The discount value deducted from the total amount.
        coupon (optional): A discount coupon applied to the order.
        status: The current status of the order (e.g., waiting, successful, canceled).
        description (optional): Additional details or customer notes about the order.
        created_at: The timestamp when the order was created.
        updated_at: The timestamp when the order was last modified.

    Methods:
        customer(): Returns the customer associated with the order.
        validate_customer(): Ensures an order has only one type of customer (online or in-person).
        validate_discount(): Ensures coupon validity and verifies applied discount accuracy.
        validate_price(): Calculates total price and enforces validation rules on amount payable.
        save(): Cleans data and determines the order type before saving.
    """
    ORDER_TYPE = [("in_person", "حضوری"), ("online", "آنلاین")]
    PAYMENT_METHOD = [("cash", "نقد"), ("credit_card", "کارت-بانکی"), ("online", "درگاه")]
    STATUS_TYPES = [("on_hold", "در-انتظار-ثبت"), ("waiting", "در-انتظار-پرداخت"), ("successful", "پرداخت-موفق"), ("failed", "پرداخت-ناموفق"), ("shipped", "ارسال-شده"), ("completed", "سفارش-تکمیل-شده"), ("canceled", "سفارش-لغو-شده"), ("refunded", "بازپرداخت-شده")]
    
    order_number = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Order Number")
    online_customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="Order_online_customers", verbose_name="Online Customer")
    in_person_customer = models.ForeignKey(InPersonCustomer, on_delete=models.CASCADE, blank=True, null=True, related_name="Order_in_person_customers", verbose_name="In-Person Customer")
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE, verbose_name="Order Type")
    shopping_cart = models.OneToOneField(ShoppingCart, on_delete=models.CASCADE, related_name="Order_shopping_cart", verbose_name="Shopping Cart")
    delivery_schedule = models.ForeignKey(DeliverySchedule, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Delivery Schedule")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Coupon")
    discount_applied = models.IntegerField(default=0, verbose_name="Discount")
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD, verbose_name="Payment Method")
    total_amount = models.PositiveIntegerField(default=0, verbose_name="Total Amount")
    amount_payable = models.PositiveIntegerField(default=0, verbose_name="Amount Payable")
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default="on_hold", verbose_name="Status")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    def customer(self):
        return self.online_customer if self.online_customer else self.in_person_customer
    
    def generate_order_number(self):
        return f"ORD-{localtime(now()).strftime('%Y%m%d')}-{self.id:06d}"
    
    def restore_stock(self):
        if self.status == "canceled":
            with transaction.atomic():
                for item in CartItem.objects.filter(cart=self.shopping_cart):
                    Warehouse.objects.create(
                        product=item.product,
                        warehouse_type="input",
                        stock=item.quantity,
                        price=item.product.price
                    )
                    
    def __str__(self):
        return f"Order {self.id} by {self.customer()} ({self.get_order_type_display()})" if self.customer() else f"Order {self.id} ({self.get_order_type_display()})"

    def clean(self):
        self.validate_customer()
        self.validate_price()
        self.validate_discount()
    
    def validate_customer(self):
        if not self.online_customer and not self.in_person_customer:
            raise ValidationError("سبد خرید حتما باید دارای کابر آنلاین یا کاربر حضوری باشد.")
        if self.online_customer and self.in_person_customer:
            raise ValidationError("سبد خرید نمیتواند هم کاربر آنلاین داشته باشد و هم کاربر حضوری.")
    
    def validate_discount(self):
        if self.discount_applied:
            if not self.coupon:
                raise ValidationError("کد تخفیف یافت نشد.")
            try:
                if not self.coupon.is_valid():
                    raise ValidationError("این کد تخفیف معتبر نیست و یا منقضی شده است.")
                expected_discount = (self.total_amount * self.coupon.discount_percentage) / 100
                if self.discount_applied != expected_discount:
                    raise ValidationError("میزان تخفیف با میزان تخفیف مورد انتظار یکسان نمی باشد.")
            except (ValidationError, Exception) as error:
                raise ValidationError(f"Validation error while applying discount: {str(error)}")
            
    def validate_price(self):
        try:
            if not self.shopping_cart:
                raise ValidationError("سبد خریدی انتخاب نشده است.")
            cart_price = self.shopping_cart.total_price
            delivery_cost = self.delivery_schedule.delivery_cost if self.delivery_schedule else 0
            self.total_amount = cart_price + delivery_cost
            if not self.discount_applied:
                self.amount_payable = self.total_amount
            if self.amount_payable <= 0:
                raise ValidationError("مبلغ قابل پرداخت نمی تواند صفر یا منفی باشد.")
        except ShoppingCart.DoesNotExist:
            raise ValidationError("سبد خرید انتخابی موجود نیست.")
        except Exception as error:
            raise ValidationError(f"An error occurred while validating the price: {str(error)}")

    def save(self, *args, **kwargs):
        if not self.order_type:
            if self.online_customer:
                self.order_type = "online"
            elif self.in_person_customer:
                self.order_type = "in_person"
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [models.Index(fields=["online_customer"]), models.Index(fields=["in_person_customer"]), models.Index(fields=["status"]), models.Index(fields=["order_type"])]


#====================================== Transaction Model =============================================

class Transaction(models.Model):
    """
    Represents a financial transaction associated with an order and makes payment through a gateway.

    Attributes:
        user: The user who initiated the transaction.
        order: The order linked to this payment transaction.
        amount: The amount charged for the transaction, provide for the gateway.
        gateway: Optional gateway identifier.
        reference_id: A unique identifier for the transaction assigned by the gateway (gateway web service).
        is_paid: Indicates whether the transaction was completed successfully.
        created_at: The timestamp when the transaction record was created.

    Methods:
        validate_amount(): Ensures the transaction amount matches the expected order payable amount.
        validate_payment(): Updates the order status and creates a delivery entry upon successful payment.
    """
    TRANSACTION_TYPES = [("payment", "پرداخت"), ("deposit", "واریز"), ("refund", "بازپرداخت")]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, blank=True, null=True, related_name="Transaction_wallet", verbose_name="Wallet")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="Transaction_order", verbose_name="Order")
    amount = models.PositiveIntegerField(verbose_name="Amount") 
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default="payment", verbose_name="Type")
    gateway = models.CharField(max_length=30, blank=True, null=True, verbose_name="Gateway")
    reference_id = models.CharField(max_length=50, unique=True, verbose_name="Reference ID")  
    is_paid = models.BooleanField(default=False, verbose_name="Is Paid")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    # content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    # object_id = models.PositiveIntegerField(null=True)
    # related_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        wallet_info = f"Wallet {self.wallet.id}" if self.wallet else "No Wallet"
        return f"{self.type} of {self.amount} for {wallet_info}"
    
    def clean(self):
        self.validate_amount()
        
    def validate_amount(self):
        self.amount = self.order.amount_payable
        if self.amount != self.order.amount_payable:
                raise ValidationError(f"مبلغ قابل پرداخت ({self.amount}) با سفارش {self.order.id} و مبلغ ({self.order.amount_payable}) یکسان نمی باشد.")
                   
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
            
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        indexes = [models.Index(fields=["order"]), models.Index(fields=["reference_id"]), models.Index(fields=["created_at"])]
    
    
#====================================== Refund Model ===================================================

class Refund(models.Model):
    """
    Represents a refund request and its processing lifecycle for a previously paid order.

    Attributes:
        user: The user who initiated the refund request.
        order: The order associated with the refund.
        amount: The amount to be refunded, typically equal to the order's payable amount.
        method: The refund method used (e.g., wallet credit or bank transfer).
        status: The current status of the refund (requested, approved, or completed).
        reason: Optional explanation for why the refund was requested (e.g., cancellation, product issue).
        created_at: Timestamp when the refund was requested.
        processed_at: Timestamp when the refund was completed.

    Methods:
        validate_amount(): Ensures the refund amount matches the original order's payable amount.
        clean(): Validates refund data before saving.
    """
    METHOD = [("wallet", "کیف-پول"), ("bank", "انتقال-بانکی")]
    STATUS = [("requested", "درخواست-شده"), ("approved", "تایید-شده"), ("completed", "تکمیل-شده")]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, blank=True, null=True, related_name="Refund_wallet", verbose_name="Wallet")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="Refund_order", verbose_name="Order")
    amount = models.PositiveIntegerField(verbose_name="Amount")
    method = models.CharField(max_length=20, choices=METHOD, default="wallet", verbose_name="Method")
    status = models.CharField(max_length=20, choices=STATUS, default="requested", verbose_name="Status")
    reason = models.TextField(blank=True, null=True, verbose_name="Reason")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name="Processed At")

    def __str__(self):
        return f"Refund for Order {self.order.id} - {self.amount} ({self.status})"

    def clean(self):
        self.validate_amount()
        
    def validate_amount(self):
        self.amount = self.order.amount_payable
        if self.amount != self.order.amount_payable:
                raise ValidationError(f"مبلغ قابل پرداخت ({self.amount}) با سفارش {self.order.id} و مبلغ ({self.order.amount_payable}) یکسان نمی باشد.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
            
    class Meta:
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"
        indexes = [models.Index(fields=["order"]), models.Index(fields=["method"]), models.Index(fields=["status"])]
    
    
#====================================== Delivery Model ================================================

class Delivery(models.Model):
    """
    Represents the shipment and delivery details of an order.

    Attributes:
        order: The order linked to this delivery record.
        status: The current delivery status (e.g., pending, shipped, delivered).
        tracking_id: The unique tracking number assigned to the delivery by Transaction model.
        postman: The name of the delivery person handling the shipment.
        shipped_at: The timestamp when the order is shipped.
        delivered_at: The timestamp when the order is successfully delivered to a customer and tracking_id is filled.
    """
    STATUS_DELIVERY = [("pending", "در-انتظار-ارسال"), ("shipped", "ارسال-شده"), ("delivered", "تحویل-شده")]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="Delivery_order", verbose_name="Order")
    status = models.CharField(max_length=20, choices=STATUS_DELIVERY, default="pending", verbose_name="Status Delivery")
    tracking_id = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Tracking Number")
    postman = models.CharField(max_length=20, null=True, blank=True, verbose_name="Postman Name")
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name="Shipped At")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Delivered At")

    def __str__(self):
        return f"Delivery for Order {self.order.id}"
        
    class Meta:
        verbose_name = "Delivery"
        verbose_name_plural = "Deliveries"
        indexes = [models.Index(fields=["order"]), models.Index(fields=["status"]), models.Index(fields=["tracking_id"]), models.Index(fields=["delivered_at"])]
        
        
#====================================== UserView Model ================================================

class UserView(models.Model):
    """
    Represents a user's interaction with a product by tracking view count and last seen time.
    This model records how frequently a user views a specific product, providing insight into user engagement and product popularity.

    Attributes:
        user (User): The authenticated user who viewed the product.
        product (Product): The product that was accessed.
        view_count (int): The total number of times the user has viewed the product.
        last_seen (datetime): The timestamp of the most recent view event.  
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="UserView_user", verbose_name="User")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="UserView_product", verbose_name="Product")
    view_count = models.PositiveIntegerField(default=1, verbose_name="View Count")  
    last_seen = models.DateTimeField(auto_now_add=True, verbose_name="Last Seen")
    
    def __str__(self):
        return f"{self.user} viewed {self.product.name} {self.view_count} times" if self.user else f"Anonymous viewed {self.product.name} {self.view_count} times"
    
    class Meta:
        verbose_name = "User View"
        verbose_name_plural = "User Views"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["product"])
        ]
        
        
#====================================== Rating Model ==================================================

class Rating(models.Model):
    """
    Represents a user's rating and review of a product.
    This model stores user feedback by capturing both numeric ratings and optional written reviews.

    Attributes:
        user (User): The user who provided the rating.
        product (Product): The product that was rated.
        rating (int): The rating given by the user, restricted to a scale of 1-5.
        review (str, optional): An optional review text describing the user's experience.
        created_at (datetime): The timestamp when the rating was recorded.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Rating_user", verbose_name="User")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="Rating_product", verbose_name="Product")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Rating")
    review = models.TextField(null=True, blank=True, verbose_name="Review")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"Rating of {self.rating} for {self.product.name} by {self.user.username}"
    
    class Meta:
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["product"]),
            models.Index(fields=["rating"])
        ]
        constraints = [
        models.UniqueConstraint(fields=["user", "product"], name="unique_user_product_rating")]
        
        
#====================================== Notification Model ============================================

class Notification(models.Model):
    """
    Represents a notification for a user.

    Attributes:
        user (User): The user receiving the notification.
        message (str): The content of the notification.
        type (str): The type of notification (e.g., order, promotion, system).
        related_object (GenericForeignKey): A generic reference to the related object (e.g., Order, Product).
        is_read (bool): Whether the notification has been read by the user.
        created_at (datetime): The timestamp when the notification was created.
    """
    TYPES = [("order", "Order Update"), ("promotion", "Promotion"), ("system", "System Alert")]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Notification_user", verbose_name="User")
    message = models.TextField(verbose_name="Message")
    type = models.CharField(max_length=20, choices=TYPES, verbose_name="Type")
    is_read = models.BooleanField(default=False, verbose_name="Is Read")
    related_object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('related_object_type', 'related_object_id')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}"
    
    
#======================================================================================================