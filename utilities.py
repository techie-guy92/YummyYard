from django.core.validators import RegexValidator
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from re import compile
from random import choice
from string import ascii_letters, digits
from django.contrib.auth import get_user_model
from users_constant import *
from products_constant import *


"""
Module for utility functions and reusable components.
"""

#======================================= Needed Methods =====================================

passwordRe = compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*]).{8,}$")
password_validator = RegexValidator(regex=passwordRe, message="رمز عبور باید متشکل از حروف کوچک، بزرگ و عدد باشد و همچنین هشت رقم داشته باشد.", code="invalid_password")
emailRe = compile(r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$")
email_validator = RegexValidator(regex=emailRe, message="ایمیل معتبر نیست.", code="invalid_email")



def email_sender(subject, message, HTML_Content, to):
    """
    Send an email with HTML content.
    """
    
    sender = settings.EMAIL_HOST_USER
    message = EmailMultiAlternatives(subject, message, sender, to)
    message.attach_alternative(HTML_Content, "text/html")
    message.send()



def code_generator(count):
    """
    Generate a random code of specified length.
    """
    
    chars = list(ascii_letters + digits)
    code = "".join([choice(chars) for _ in range(count)])
    return code
         


def replace_dash_to_space(title):
    """
    Replace spaces with dashes in a given title.
    """
    
    new_title = "".join([eliminator.replace(" ", "-") for eliminator in title])
    return new_title.lower()
    


User = get_user_model()
    
    
def create_test_users():
    """
    Create and return test users.
    """
    
    user_1 = User.objects.create_user(**primary_user_1)
    user_1.is_active = True
    user_1.is_admin = True
    user_1.is_superuser = True
    user_1.save(update_fields=["is_active", "is_admin", "is_superuser"])
    user_2 = User.objects.create_user(**primary_user_2)
    user_2.is_active = True
    user_2.is_premium = True
    user_2.save(update_fields=["is_active", "is_premium"])
    user_3 = User.objects.create_user(**primary_user_3)
    user_3.is_active = True
    user_3.save(update_fields=["is_active"])
    user_4 = User.objects.create_user(**primary_user_4)    
    return user_1, user_2, user_3, user_4


def create_test_categories():
    """
    Create and return test categories.
    """
    
    from main.models import Category
    category_1 = Category.objects.create(name=primary_category_1["name"])
    category_2 = Category.objects.create(name=primary_category_2["name"])
    category_3 = Category.objects.create(name=primary_category_3["name"], parent=category_2)
    category_4 = Category.objects.create(name=primary_category_4["name"], parent=category_2)
    category_5 = Category.objects.create(name=primary_category_5["name"], parent=category_2)
    category_6 = Category.objects.create(name=primary_category_6["name"], parent=category_3)
    category_7 = Category.objects.create(name=primary_category_7["name"], parent=category_3)
    return category_1, category_2, category_3, category_4, category_5, category_6, category_7


def create_test_products():
    """
    Create and return test products.
    """
    
    from main.models import Product
    # It returns a tuple, so indexing starts at 0 and last one is 6.
    categories = create_test_categories()       
    product_1 = Product.objects.create(name=primary_product_1["name"], category=categories[4], price=primary_product_1["price"])  
    product_2 = Product.objects.create(name=primary_product_2["name"], category=categories[4], price=primary_product_2["price"])
    product_3 = Product.objects.create(name=primary_product_3["name"], category=categories[2], price=primary_product_3["price"])
    product_4 = Product.objects.create(name=primary_product_4["name"], category=categories[3], price=primary_product_4["price"])
    product_5 = Product.objects.create(name=primary_product_5["name"], category=categories[5], price=primary_product_5["price"])
    product_6 = Product.objects.create(name=primary_product_6["name"], category=categories[5], price=primary_product_6["price"])
    product_7 = Product.objects.create(name=primary_product_7["name"], category=categories[6], price=primary_product_7["price"])
    product_8 = Product.objects.create(name=primary_product_8["name"], category=categories[6], price=primary_product_8["price"])
    return product_1, product_2, product_3, product_4, product_5, product_6, product_7, product_8


#============================================================================================