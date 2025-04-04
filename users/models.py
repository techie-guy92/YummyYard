from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils.timezone import now, localtime
from datetime import timedelta
from django.conf import settings
from os.path import splitext
from uuid import uuid4


#======================================= Needed Method ================================================

def upload_to(instance, filename):
    file_name, ext = splitext(filename)
    new_filename = f"{uuid4()}{ext}"
    user = instance.user
    full_name = user.get_full_name().replace(" ", "-")
    return f"images/users/{full_name}/{new_filename}"

    
#====================================== CustomUserManager Model =======================================

class CustomUserManager(BaseUserManager):
    """
    Custom manager for creating regular and super users.
    """
    
    def create_user(self, username, first_name, last_name, email, password = None):
        """
        Creates and saves a regular user with the given details.

        Parameters:
        username (str): The username of the user
        first_name (str): The first name of the user
        last_name (str): The last name of the user
        email (str): The email address of the user
        password (str, optional): The password of the user
        
        Returns:
        CustomUser: The created user object
        """
        if not email:
            raise ValueError("وارد کردن ایمیل ضروری است.")
        
        user = self.model(
            username = username,
            first_name = first_name.capitalize(),
            last_name = last_name.capitalize(),
            email = self.normalize_email(email)
        )
        
        user.set_password(password)
        user.user_type = "user"
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, first_name, last_name, email, password = None):
        """
        Creates and saves a superuser with the given details.

        Parameters:
        username (str): The username of the user
        first_name (str): The first name of the user
        last_name (str): The last name of the user
        email (str): The email address of the user
        password (str, optional): The password of the user

        Returns:
        CustomUser: The created superuser object
        """
        user = self.create_user(
            username = username,
            first_name = first_name, 
            last_name = last_name,
            email = email,
            password = password 
        )
        
        user.is_active = True
        user.is_admin = True
        user.is_superuser = True
        user.user_type = "backend"
        user.save(using=self._db)
        return user


#======================================= CustomUser Model =============================================

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that extends AbstractBaseUser and PermissionsMixin.

    Attributes:
    username (str): The username of the user
    first_name (str): The first name of the user
    last_name (str): The last name of the user
    email (str): The email address of the user
    user_type (str): The type of user
    is_active (bool): Indicates if the user is active
    is_premium (bool): Indicates if the user is a premium user
    is_admin (bool): Indicates if the user is an admin
    is_superuser (bool): Indicates if the user is a superuser
    joined_at (datetime): The date and time when the user joined
    updated_at (datetime): The date and time when the user was last updated
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

    # groups = models.ManyToManyField(Group, related_name="customuser_set", blank=True, verbose_name="Groups")
    # user_permissions = models.ManyToManyField(Permission, related_name="customuser_permissions_set", blank=True, verbose_name="User Permissions")

    @property
    def is_staff(self):
        """
        Indicates if the user is staff (admin).

        Returns:
        bool: True if the user is admin, False otherwise
        """
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

    Attributes:
    user (CustomUser): The user associated with the profile
    phone (str): The phone number of the user
    gender (str): The gender of the user
    address (str, optional): The address of the user
    bio (str, optional): The bio of the user
    picture (ImageField, optional): The profile picture of the user
    """
    
    GENDER_TYPE = [("male","Male"), ("female","Female"), ("other","Other")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="UserProfile_user", verbose_name="User")
    phone = models.CharField(max_length=12, unique=True, verbose_name="Phone")
    gender = models.CharField(max_length=10, choices=GENDER_TYPE, default="other", verbose_name="Gender")
    address = models.TextField(null=True, blank=True, verbose_name="Address")
    bio = models.TextField(null=True, blank=True, verbose_name="Bio")
    picture = models.ImageField(upload_to=upload_to, null=True, blank=True, verbose_name="Picture")
    
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


#====================================== PremiumSubscription Model =====================================

class PremiumSubscription(models.Model):
    """
    Model for storing premium subscription details of a user.

    Attributes:
    user (CustomUser): The user associated with the premium subscription
    start_date (date): The start date of the subscription
    expiry_date (date): The expiry date of the subscription
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="PremiumSubscription_user", verbose_name="User")
    start_date = models.DateTimeField(verbose_name="Start Date")
    expiry_date = models.DateTimeField(verbose_name="Expiry Date")
    
    def __str__(self):
        return f"{self.user.username}"

    def is_expired(self):
        """
        Checks if the subscription has expired.

        Returns:
        bool: True if the subscription has expired, False otherwise
        """
        return self.expiry_date < localtime(now())
   
    class Meta:
        verbose_name = "PremiumSubscription"
        verbose_name_plural = "PremiumSubscriptions"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["expiry_date"]),
        ]


#====================================== Payment Model =================================================

class Payment(models.Model):
    """
    Model for storing payment details of a user.

    Attributes:
    user (CustomUser): The user associated with the payment
    amount (DecimalField): The payment amount
    payment_id (str, optional): The payment ID
    is_successful (bool): Indicates whether the payment was completed successfully
    payment_date (datetime): The date and time of the payment
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Payment_user", verbose_name="User")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=70.00, verbose_name="Amount Payable")
    payment_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="Payment ID")
    is_sucessful = models.BooleanField(default=False, verbose_name="Is Successful")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Payment Date")
    
    def __str__(self):
        return f"Payment {self.payment_id} for {self.user.username}"
    
    def process_payment(self):
        """
        Processes the payment and updates the user's premium subscription.

        Returns:
        None
        """
        current_date = localtime(now())
        extended_date = current_date + timedelta(days=90)
        
        if self.is_sucessful:
            with transaction.atomic():
                self.user.is_premium = True
                premium_sub, created = PremiumSubscription.objects.get_or_create(user=self.user, defaults={
                    "start_date": current_date,
                    "expiry_date": extended_date
                })
                
                if not created:
                    premium_sub.start_date = current_date
                    premium_sub.expiry_date = extended_date
                self.user.save()
                premium_sub.save()

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["payment_id"]),
            models.Index(fields=["payment_date"]),
        ]


#======================================================================================================
