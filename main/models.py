from django.db import models, transaction
from django.db.models import Sum, Count
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from logging import getLogger
from django.utils.timezone import now, localtime
from django.conf import settings
from os.path import splitext
from uuid import uuid4
from django.utils.text import slugify
from utilities import code_generator
from users.models import InPersonCustomer


#======================================= Needed Method ================================================

logger = getLogger(__name__)


def upload_to(instance, filename):
    file_name, ext = splitext(filename)
    new_filename = f"{uuid4()}{ext}"
    
    if isinstance(instance, Category):
        return f"images/categories/{slugify(instance.name, allow_unicode=True)}/{new_filename}"
    elif isinstance(instance, Product):
        return f"images/products/{slugify(instance.name, allow_unicode=True)}/{new_filename}"
    elif isinstance(instance, Gallery) and instance.product:
        return f"images/gallery/{slugify(instance.product.name, allow_unicode=True)}/{new_filename}"
    else:
        return f"images/others/{new_filename}"


#====================================== Category Model ================================================

class Category(models.Model):
    """
    Represents a product category in the system.

    Attributes:
        name (str): The name of the category.
        parent (Category): A reference to the parent category, supporting hierarchical organization.
        slug (str): A unique slug for the category, used for URLs.
        description (str): An optional description of the category.
        image (ImageField): An optional image for the category.
        created_at (datetime): The timestamp when the category was created.
        updated_at (datetime): The timestamp when the category was last updated.
    """
    
    name = models.CharField(max_length=100, verbose_name="Category")
    parent = models.ForeignKey("Category", on_delete=models.CASCADE, related_name="Category_parent", null=True, blank=True, verbose_name="Parent")
    slug = models.SlugField(unique=True, editable=False, verbose_name="Slug")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    image = models.ImageField(upload_to=upload_to, null=True, blank=True, verbose_name="Image")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name="Updated At")

    def __str__(self):
        return f"{self.name}"
    
    def clean(self):
        self.validate_parent()
          
    def validate_parent(self):
        if self.parent and self.parent.id == self.id:
            raise ValidationError("Category cannot be its own parent.")
        
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
    Represents a product available for sale.

    Attributes:
        name (str): The name of the product.
        category (Category): The category to which the product belongs.
        slug (str): A unique slug for the product, used for URLs.
        price (int): The price of the product.
        description (str): An optional description of the product.
        image (ImageField): An optional image for the product.
        created_at (datetime): The timestamp when the product was created.
        updated_at (datetime): The timestamp when the product was last updated.
    """
    
    name = models.CharField(max_length=250, verbose_name="Product") 
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="Product_category", verbose_name="Category")
    slug = models.SlugField(unique=True, editable=False, verbose_name="Slug")
    price = models.PositiveIntegerField(default=0, verbose_name="Price")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    image = models.ImageField(upload_to=upload_to, null=True, blank=True, verbose_name="Image")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name="Updated At")
    
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

    Attributes:
        product (Product): The product associated with the gallery.
        image (ImageField): An image for the product.
    """
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="Gallery_product", verbose_name="Product")
    image = models.ImageField(upload_to=upload_to, verbose_name="Image")
    
    class Meta:
        verbose_name = "Gallery"
        verbose_name_plural = "Galleries"


#====================================== Warehouse Model ===============================================

class Warehouse(models.Model):
    """
    Represents stock management for a product.

    Attributes:
        product (Product): The product in the warehouse.
        warehouse_type (str): The type of warehouse entry (e.g., input, output, defective).
        stock (int): The stock quantity of the product.
        is_active (bool): Whether the warehouse entry is active based on stock availability.
        price (int): The price of the product in the warehouse.
        created_at (datetime): The timestamp when the warehouse entry was created.
        updated_at (datetime): The timestamp when the warehouse entry was last updated.
    """
    
    WAREHOUSE_TYPE = [("input", "Input"), ("output", "Output"), ("defective", "Defective"), ("sent_back", "Sent Back")]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="Warehouse_product", verbose_name="Product")
    warehouse_type = models.CharField(max_length=10, choices=WAREHOUSE_TYPE, default="input", verbose_name="Warehouse Type")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")  
    is_available = models.BooleanField(default=True, editable=False, verbose_name="Is Available") 
    price = models.IntegerField(default=0, verbose_name="Price")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name="Updated At")
    
    def __str__(self):
        return f"{self.product} - {self.stock}"
        
    @staticmethod
    def total_stock(product):
        input_stock = Warehouse.objects.filter(product=product, warehouse_type="input").aggregate(total=Sum("stock"))["total"] or 0
        output_stock = Warehouse.objects.filter(product=product, warehouse_type="output").aggregate(total=Sum("stock"))["total"] or 0
        defective_stock = Warehouse.objects.filter(product=product, warehouse_type="defective").aggregate(total=Sum("stock"))["total"] or 0
        return input_stock - (output_stock + defective_stock)
    
    class Meta:
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"
        indexes = [models.Index(fields=["product"]), models.Index(fields=["warehouse_type"]), models.Index(fields=["stock"]), models.Index(fields=["created_at"])]
        
        
#====================================== Coupon Model ==================================================

class Coupon(models.Model):
    """
    Represents a discount coupon.

    Attributes:
        code (str): A unique code for the coupon.
        discount_percentage (Decimal): The discount percentage for the coupon.
        valid_from (datetime): The date and time when the coupon becomes valid.
        valid_to (datetime): The date and time when the coupon expires.
        is_active (bool): Whether the coupon is currently active.
    """
    
    code = models.CharField(max_length=10, blank=True, verbose_name="Code")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="Coupon_category", null=True, blank=True, verbose_name="Category")
    discount_percentage = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(10), MaxValueValidator(50)], verbose_name="Discount Percentage")
    max_usage = models.PositiveIntegerField(default=1, verbose_name="Maximum Usage")
    usage_count = models.PositiveIntegerField(default=0, editable=False, verbose_name="Usage Count")
    valid_from = models.DateTimeField(verbose_name="Valid From")
    valid_to = models.DateTimeField(verbose_name="Valid To")
    is_active = models.BooleanField(default=False, verbose_name="Is Active")
    
    def __str__(self):
        return f"{self.code}"
        
    def is_expired(self):
        return self.valid_to < localtime(now())
    
    def is_valid(self):
        return self.is_active and not self.is_expired() and self.usage_count < self.max_usage
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = code_generator(5)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        indexes = [models.Index(fields=["is_active"]), models.Index(fields=["valid_from"]), models.Index(fields=["valid_to"])]
        
        
#====================================== Wishlist Model ================================================

class Wishlist(models.Model):
    """
    Represents a user's wishlist of products.

    Attributes:
        user (User): The user who owns the wishlist.
        product (Product): The product added to the wishlist.
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Wishlist_user", verbose_name="User")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="Wishlist_product", verbose_name="Product")
   
    def __str__(self):
        return f"Wishlist of {self.user.username}"

    def get_product_price(self):
        return self.product.price
    
    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"
        indexes = [models.Index(fields=["product"])]
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_wishlist_item")]
        

#====================================== ShoppingCart Model ============================================

class ShoppingCart(models.Model):
    """
    Represents a user's shopping cart.

    This model tracks the items and their total amount for a user during an ongoing shopping session.

    Attributes:
        online_customer (User): The online user who owns the shopping cart (optional).
        in_person_customer (InPersonCustomer): The in-person customer who owns the shopping cart (optional).
        products (ManyToManyField): The products in the shopping cart, linked through CartItem.
        total_price (int): The total price of all items in the shopping cart.
    """
    
    online_customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="ShoppingCart_online_customers", verbose_name="Online Customer")
    in_person_customer = models.ForeignKey(InPersonCustomer, on_delete=models.CASCADE, blank=True, null=True, related_name="ShoppingCart_in_person_customers", verbose_name="In-Person Customer")
    products = models.ManyToManyField(Product, through="CartItem", related_name="ShoppingCart_products", verbose_name="Products")
    total_price = models.PositiveIntegerField(default=0, verbose_name="Total Price")

    def customer(self):
        return self.online_customer if self.online_customer else self.in_person_customer
    
    def __str__(self):
        return f"{self.id} - {self.online_customer.username if self.online_customer else self.in_person_customer.first_name+' '+self.in_person_customer.last_name}"

    def clean(self):
        self.validate_customer()
        
    def validate_customer(self):
        if not self.online_customer and not self.in_person_customer:
            raise ValidationError("A shopping cart must have either an online or in-person customer.")
        if self.online_customer and self.in_person_customer:
            raise ValidationError("A shopping cart cannot have both an online and in-person customer.")

    def calculate_total_price(self):
        return sum(item.grand_total for item in CartItem.objects.filter(cart=self))
     
    def place_order(self):
        with transaction.atomic():
            for item in CartItem.objects.filter(cart=self):
                Warehouse.objects.create(
                    product=item.product,
                    warehouse_type="output",
                    stock=item.quantity,
                    price=item.product.price,
                    )
    
    def clear_cart(self):
        CartItem.objects.filter(cart=self).delete()
        self.total_price = 0
        self.save(update_fields=["total_price"])
        
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
        indexes = [models.Index(fields=["online_customer"]), models.Index(fields=["in_person_customer"])]
        
class CartItem(models.Model):
    """
    Represents an individual item in a shopping cart.

    This model tracks the product, its quantity, and the calculated total price for the given quantity.

    Attributes:
        cart (ShoppingCart): The shopping cart to which this item belongs.
        product (Product): The product being purchased.
        quantity (int): The quantity of the product in the cart.
        total_price (int): The total price of the product based on its quantity.
    """
    
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name="CartItem_cart", verbose_name="Cart")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="CartItem_product", verbose_name="Product")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    grand_total = models.PositiveIntegerField(default=0, verbose_name="Grand Total")
    
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
            raise ValidationError("Quantity must be greater than zero.")
    
    def validate_stock(self):
        total_stock = Warehouse.total_stock(product=self.product) 
        if self.quantity > total_stock:
            raise ValidationError(f"Not enough stock for {self.product.name}. Requested: {self.quantity}, Available: {total_stock}")

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
    Represents a delivery schedule with specified dates and time slots.

    This model manages available delivery slots, including the day of the week,
    the exact delivery date, time ranges, and their capacity for deliveries.

    Attributes:
        day (str): The day of the week for the delivery slot.
        date (DateField): The specific date of the delivery slot.
        time (str): The time of the delivery slot (e.g., 8 - 10).
        is_available (bool): Indicates whether this delivery slot is currently available.
        total_capacity (int): Maximum allowed deliveries for this slot.
        current_capacity (int): Number of deliveries currently booked for this slot.
    """

    TIMES = [("8_10", "8 - 10"), ("10_12", "10 - 12"), ("12_14", "12 - 14"), ("14_16", "14 - 16"), ("16_18", "16 - 18"), ("18_20", "18 - 20"), ("20_22", "20 - 22")]
    DELIVERY_METHODS = [("normal", "Normal Shipping"), ("fast", "Fast Shipping"), ("postal", "Postal Delivery")]
    MAX_DAYS_AHEAD = 7
    MAX_CAPACITY_DELIVERY_NORMAL = 5
    MAX_CAPACITY_DELIVERY_FAST = 3  
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="DeliverySchedule_user", verbose_name="User")
    shopping_cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name="DeliverySchedule_shopping_cart", verbose_name="Shopping Cart")
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS, verbose_name="Delivery Method")
    date = models.DateField(verbose_name="Delivery Date")
    day = models.CharField(max_length=10, editable=False, verbose_name="Day of the Week")
    time = models.CharField(max_length=10, choices=TIMES, verbose_name="Time")
    delivery_cost = models.PositiveIntegerField(default=0, verbose_name="Delivery Cost")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name="Updated At")

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
                raise ValidationError("User is required.")
            if self.user and self.shopping_cart and self.user != self.shopping_cart.online_customer:
                raise ValidationError("User and ShoppingCart's online_customer must be the same.")
        except Exception as error:
            raise ValidationError(f"An error occurred while validating the order: {str(error)}")
    
    def validate_timeframe(self):
        crr_datetime = localtime(now())
        crr_date = crr_datetime.date()
        crr_hour = crr_datetime.hour
        if self.date < crr_date:
            raise ValidationError("Delivery cannot be scheduled in the past. Please select a future date.")
        if (self.date - crr_date).days > self.MAX_DAYS_AHEAD:
            raise ValidationError(f"Delivery cannot be scheduled more than {self.MAX_DAYS_AHEAD} days from today.")
        if self.date == crr_date:
            start_hour = int(self.time.split("_")[0])
            if start_hour <= crr_hour + 4:
                raise ValidationError(f"The selected timeframe ({self.time}) is unavailable. Please select a timeframe starting after {crr_hour + 4}:00. If no later timeframes are available today, please choose a delivery slot for tomorrow.")
                
    # def validate_delivery_slot(self):
    #     total_booked_normal = DeliverySchedule.objects.filter(date=self.date, time=self.time, delivery_method="normal").count()
    #     total_booked_fast = DeliverySchedule.objects.filter(date=self.date, time=self.time, delivery_method="fast").count()
    #     if total_booked_normal >= self.MAX_CAPACITY_DELIVERY_NORMAL:  
    #         raise ValidationError("Normal delivery slot is fully booked for this timeframe. Please select other timeframes.")
    #     if total_booked_fast >= self.MAX_CAPACITY_DELIVERY_FAST:  
    #         raise ValidationError("Fast delivery slot is fully booked for this timeframe. Please select other timeframes.")
        
    def validate_delivery_slot(self):
        total_booked = (DeliverySchedule.objects.filter(date=self.date, time=self.time).values("delivery_method").annotate(count=Count("delivery_method")))
        total_booked_dict = {entry["delivery_method"]: entry["count"] for entry in total_booked}
        if total_booked_dict.get("normal", 0) >= self.MAX_CAPACITY_DELIVERY_NORMAL:
            raise ValidationError("Normal delivery slot is fully booked for this timeframe. Please select other timeframes.")
        if total_booked_dict.get("fast", 0) >= self.MAX_CAPACITY_DELIVERY_FAST:
            raise ValidationError("Fast delivery slot is fully booked for this timeframe. Please select other timeframes.")
        
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
    Represents an order made by a customer.

    This model includes details about the customer, the payment method, delivery method,
    the total amount payable, and the status of the order.

    Attributes:
        online_customer (User): The online user who placed the order (optional).
        in_person_customer (InPersonCustomer): The in-person customer who placed the order (optional).
        order_type (str): The type of order (e.g., 'in_person', 'online').
        payment_method (str): The payment method used (e.g., 'cash', 'credit_card').
        delivery_method (str): The selected delivery method (e.g., 'normal', 'fast').
        status (str): The current status of the order (e.g., 'waiting', 'successful').
        discount_applied (Decimal): The discount applied to the order (if any).
        amount_payable (int): The total amount to be paid after discount.
        description (str): Additional details or notes about the order.
        created_at (datetime): The timestamp when the order was created.
        updated_at (datetime): The timestamp when the order was last updated.
    """
    
    ORDER_TYPE = [("in_person", "In-Person"), ("online", "Online")]
    PAYMENT_METHOD = [("cash", "Cash"), ("credit_card", "Credit-Card"), ("online", "Online")]
    STATUS_TYPES = [("on_hold", "On Hold"), ("waiting", "Waiting for Payment"), ("successful", "Successful Payment"), ("failed", "Failed Payment"), ("shipped", "Shipped"), ("completed", "Completed Order"), ("canceled", "Canceled Order"), ("refunded", "Refunded Payment")]
    
    online_customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="Order_online_customers", verbose_name="Online Customer")
    in_person_customer = models.ForeignKey(InPersonCustomer, on_delete=models.CASCADE, blank=True, null=True, related_name="Order_in_person_customers", verbose_name="In-Person Customer")
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE, verbose_name="Order Type")
    shopping_cart = models.OneToOneField(ShoppingCart, on_delete=models.CASCADE, related_name="Order_shopping_cart", verbose_name="Shopping Cart")
    delivery_schedule = models.ForeignKey(DeliverySchedule, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Delivery Schedule")
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD, verbose_name="Payment Method")
    total_amount = models.PositiveIntegerField(default=0, verbose_name="Total Amount")
    amount_payable = models.PositiveIntegerField(verbose_name="Amount Payable")
    discount_applied = models.DecimalField(max_digits=4, decimal_places=2, default=0, verbose_name="Discount Applied")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Coupon")
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default="on_hold", verbose_name="Status")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name="Updated At")
    
    def __str__(self):
        customer = self.online_customer if self.online_customer else self.in_person_customer
        return f"Order {self.id} by {customer} ({self.get_order_type_display()})" if customer else f"Order {self.id} ({self.get_order_type_display()})"

    def customer(self):
        return self.online_customer if self.online_customer else self.in_person_customer

    def clean(self):
        self.validate_customer()
        self.validate_price()
        self.validate_discount()
    
    def validate_customer(self):
        if not self.online_customer and not self.in_person_customer:
            raise ValidationError("An order must have either an online or in-person customer.")
        if self.online_customer and self.in_person_customer:
            raise ValidationError("An order cannot have both an online and in-person customer.")
    
    def validate_price(self):
        try:
            if not self.shopping_cart:
                raise ValidationError("No ShoppingCart is linked to this Order.")
            cart_price = self.shopping_cart.total_price
            delivery_cost = self.delivery_schedule.delivery_cost
            self.total_amount = cart_price + delivery_cost
            self.amount_payable = self.total_amount - self.discount_applied
            if self.amount_payable <= 0:
                raise ValidationError("amount_payable cannot be zero or negative.")
        except ShoppingCart.DoesNotExist:
            raise ValidationError("The linked ShoppingCart does not exist in the database.")
        except Exception as error:
            raise ValidationError(f"An error occurred while validating the price: {str(error)}")

    def validate_discount(self):
        if self.discount_applied:
            try:
                if self.discount_applied != self.coupon.discount_percentage:
                    raise ValidationError("discount_applied does not match the coupon's discount_percentage.")
                if not self.coupon.is_valid():
                    raise ValidationError("This coupon is no longer valid.")
                with transaction.atomic():
                    self.coupon.usage_count = models.F("usage_count") + 1
                    self.coupon.save(update_fields=["usage_count"])
                    self.coupon.refresh_from_db()
                    if self.coupon.usage_count >= self.coupon.max_usage:
                        self.coupon.is_active = False
                        self.coupon.save(update_fields=["is_active"])
            except Exception as error:
                raise ValidationError(f"Error applying discount: {str(error)}")
        
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
    Represents a financial transaction for an order.

    This model tracks payment-related information, including the amount paid,
    whether the payment is successful, and other metadata like payment IDs.

    Attributes:
        user (User): The user who initiated the transaction.
        order (Order): The order associated with this transaction.
        amount (int): The amount paid in the transaction.
        is_successful (bool): Indicates whether the payment was completed successfully.
        status_code (int): The status code returned by the payment gateway (if applicable).
        payment_id (str): The unique identifier for the transaction provided by the payment gateway.
        created_at (datetime): The timestamp when the transaction was created.
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Transaction_user", verbose_name="User")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="Transaction_order", verbose_name="Order")
    amount = models.PositiveIntegerField(verbose_name="Amount")
    payment_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Payment ID")
    is_successful = models.BooleanField(default=False, verbose_name="Is Successful")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")

    def __str__(self):
        return f"{self.payment_id}"
    
    def clean(self):
        self.validate_amount()
        self.validate_payment()
        
    def validate_amount(self):
        if self.amount != self.order.amount_payable:
                raise ValidationError(f"Transaction amount ({self.amount}) does not match the payable amount for Order {self.order.id} ({self.order.amount_payable}).")
        
    def validate_payment(self):
        if self.is_successful:
            self.order.status = "successful"
            # self.order.shopping_cart.clear_cart()
            self.order.save(update_fields=["status"])
            
            self.order.refresh_from_db()
            with transaction.atomic():
                delivery, created = Delivery.objects.get_or_create(order=self.order, defaults={
                    "tracking_id": f"{self.order.id}-{uuid4().hex[:5].upper()}", 
                    "status": "pending"
                    })
                if created:
                    logger.info(f"Created delivery {delivery.id} for order {self.order.id}")
                delivery.save() 
                    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
            
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        indexes = [models.Index(fields=["user"]), models.Index(fields=["order"]), models.Index(fields=["payment_id"]), models.Index(fields=["created_at"])]
    
    
#====================================== Delivery Model ================================================

class Delivery(models.Model):
    """
    Represents the delivery details of an order.

    Attributes:
        order (Order): The order being delivered.
        status (str): The delivery status (e.g., pending, shipped, delivered).
        tracking_id (str): The tracking number for the delivery.
        delivered_at (datetime): The actual delivery time.
    """
    
    STATUS_DELIVERY = [("pending", "Pending"), ("shipped", "Shipped"), ("delivered", "Delivered")]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="Delivery_order", verbose_name="Order")
    status = models.CharField(max_length=20, choices=STATUS_DELIVERY, default="pending", verbose_name="Status Delivery")
    tracking_id = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Tracking Number")
    postman = models.CharField(max_length=20, null=True, blank=True, verbose_name="Postman Name")
    shipped_at = models.DateTimeField(null=True, blank=True, editable=False, verbose_name="Shipped At")
    delivered_at = models.DateTimeField(null=True, blank=True, editable=False, verbose_name="Delivered At")

    def __str__(self):
        return f"Delivery for Order {self.order.id}"
        
    class Meta:
        verbose_name = "Delivery"
        verbose_name_plural = "Deliveries"
        indexes = [models.Index(fields=["order"]), models.Index(fields=["status"]), models.Index(fields=["tracking_id"]), models.Index(fields=["delivered_at"])]
        
        
#====================================== UserView Model ================================================

class UserView(models.Model):
    """
    Represents a record of a user viewing a product.

    Attributes:
        user (User): The user who viewed the product.
        product (Product): The product that was viewed.
        timestamp (datetime): The timestamp when the product was viewed.
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="UserView_user", verbose_name="User")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="UserView_product", verbose_name="Product")
    timestamp = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Viewed At")
    
    def __str__(self):
        return f"{self.user} viewed {self.product.name}" if self.user else f"Anonymous viewed {self.product.name}"
    
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

    Attributes:
        user (User): The user who rated the product.
        product (Product): The product being rated.
        rating (int): The user's rating for the product (1-5 scale).
        review (str): An optional review of the product.
        created_at (datetime): The timestamp when the rating was created.
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Rating_user", verbose_name="User")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="Rating_product", verbose_name="Product")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Rating")
    review = models.TextField(null=True, blank=True, verbose_name="Review")
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Created At")

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