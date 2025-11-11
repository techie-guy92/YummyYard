from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils.timezone import now, localtime
from datetime import timedelta
from django.conf import settings
from logging import getLogger
from media_utils import upload_to, Arvan_storage


logger = getLogger(__name__)

#====================================== CustomUserManager Model =======================================

class CustomUserManager(BaseUserManager):
    """
    Custom manager for creating regular and super users.
    """
    def create_user(self, username, first_name, last_name, email, password=None, **extra_fields):
        if not email:
            raise ValueError("وارد کردن ایمیل ضروری است.")
        if not username:
            raise ValueError("وارد کردن نام کاربری ضروری است.")
        if not first_name:
            raise ValueError("وارد کردن نام ضروری است.")
        if not last_name:
            raise ValueError("وارد کردن نام خانوادگی ضروری است.")
        
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            first_name=first_name.capitalize(),
            last_name=last_name.capitalize(),
            email=email,
            **extra_fields
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, first_name, last_name, email, password=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", "backend")
        
        if extra_fields.get("is_admin") is not True:
            raise ValueError("Superuser must have is_admin=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        return self.create_user(
            username=username, 
            first_name=first_name, 
            last_name=last_name,
            email=email,
            password=password,
            **extra_fields
        )


#======================================= CustomUser Model =============================================

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that extends AbstractBaseUser and PermissionsMixin.
    """
    USER_TYPE = [("backend","BackEnd"), ("frontend","FrontEnd"), ("admin","Admin"), ("premium","Premium"), ("user","User")]
    username = models.CharField(max_length=30, unique=True, verbose_name="Username")
    first_name = models.CharField(max_length=30, verbose_name="First Name")
    last_name = models.CharField(max_length=30, verbose_name="Last Name")
    email = models.EmailField(max_length=50, unique=True, verbose_name="Email")
    user_type = models.CharField(max_length=10, choices=USER_TYPE, default="user", verbose_name="User Type")
    is_active = models.BooleanField(default=False, verbose_name="Being Active")
    is_premium = models.BooleanField(default=False, verbose_name="Being Premium")
    is_admin = models.BooleanField(default=False, verbose_name="Being Admin")
    is_superuser = models.BooleanField(default=False, verbose_name="Being Superuser")
    joined_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Joined At")
    updated_at = models.DateTimeField(auto_now=True, editable=False, verbose_name="Updated At")

    @property
    def is_staff(self):
        return self.is_admin
    
    def __str__(self):
        return f"{self.username}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
   
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name", "email"]
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"


#====================================== UserProfile Model =============================================

class UserProfile(models.Model):
    """
    Model for storing additional user profile information.
    """
    GENDER_TYPE = [("male","Male"), ("female","Female"), ("other","Other")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="UserProfile_user", verbose_name="User")
    phone = models.CharField(max_length=12, unique=True, verbose_name="Phone")
    gender = models.CharField(max_length=10, choices=GENDER_TYPE, default="other", verbose_name="Gender")
    address = models.TextField(null=True, blank=True, verbose_name="Address")
    bio = models.TextField(null=True, blank=True, verbose_name="Bio")
    picture = models.ImageField(upload_to=upload_to, storage=Arvan_storage, null=True, blank=True, verbose_name="Picture")
    
    def __str__(self):
        return f"{self.user.username} - {self.phone}"
    
    class Meta:
        verbose_name = "UserProfile"
        verbose_name_plural = "UserProfiles"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["gender"]),
        ]
        
        
#====================================== InPersonCustomer Model ========================================

class InPersonCustomer(models.Model):
    """
    Model for placing orders for in-person customers.
    """
    first_name = models.CharField(max_length=30, verbose_name="First Name")
    last_name = models.CharField(max_length=30, verbose_name="Last Nmae")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Phone Number")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def clean(self):
       self.capitalize_full_name()
    
    def capitalize_full_name(self):
        self.first_name = self.first_name.capitalize()
        self.last_name = self.last_name.capitalize()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = "In-Person Customer"
        verbose_name_plural = "In-Person Customers"


#====================================== Wallet Model ====================================================

class Wallet(models.Model):
    """
    Represents a user's wallet for storing and managing funds.
    """
    STATUS_TYPES = [("active", "فعال"), ("frozen", "مسدود"), ("closed", "بسته‌-شده")]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallets", verbose_name="Wallet Owner")
    balance = models.PositiveIntegerField(default=0, verbose_name="Balance")
    currency = models.CharField(max_length=10, default="IRT", verbose_name="Currency")
    status = models.CharField(max_length=10, choices=STATUS_TYPES, default="active", verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"Wallet {self.id} - {self.owner.username} ({self.balance} {self.currency})"

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("مبلغ واریزی باید بیشتر از صفر باشد.")
        self.balance += amount
        self.save(update_fields=["balance"])

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("موجودی ناکافی است.")
        self.balance -= amount
        self.save(update_fields=["balance"])

    def freeze(self):
        self.status = "frozen"
        self.save(update_fields=["status"])

    def activate(self):
        self.status = "active"
        self.save(update_fields=["status"])

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        indexes = [models.Index(fields=["owner"]), models.Index(fields=["status"])]


#====================================== Payment Model =================================================

class Payment(models.Model):
    """
    Model for storing payment details of a user.
    
    Methods:
        process_payment(): Processes the payment and updates the user"s premium subscription.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Payment_user", verbose_name="User")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=70.00, verbose_name="Amount Payable")
    payment_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="Payment ID")
    is_paid = models.BooleanField(default=False, verbose_name="Is Paid")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Payment Date")
    
    def __str__(self):
        return f"Payment {self.payment_id} for {self.user.username}"
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["payment_id"]),
            models.Index(fields=["payment_date"]),
        ]
        

#====================================== PremiumSubscription Model =====================================

class PremiumSubscription(models.Model):
    """
    Model for storing premium subscription details of a user.
    
    Methods: 
        is_expired(): Checks if the subscription has expired. Returns True if the subscription has expired, False otherwise.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="PremiumSubscription_user", verbose_name="User")
    start_date = models.DateTimeField(verbose_name="Start Date")
    expiry_date = models.DateTimeField(verbose_name="Expiry Date")
    is_active = models.BooleanField(default=False, verbose_name="Is Active")
    
    def __str__(self):
        return f"{self.user.username}"

    def is_expired(self):
        return self.expiry_date < localtime(now())
             
    class Meta:
        verbose_name = "PremiumSubscription"
        verbose_name_plural = "PremiumSubscriptions"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["expiry_date"]),
        ]


#======================================================================================================
