from django_jalali.db import models as jmodels
# from django_jalali.admin import ModelAdminJalali
# from django_jalali.forms import jDateField
from khayyam import JalaliDate, JalaliDatetime, TehranTimezone
from datetime import timedelta
import jdatetime
import datetime
from config.storages import ArvanCloudStorage
from os.path import splitext
from uuid import uuid4
from django.utils.text import slugify


# ===================================================================

# Model fields
created_date = jmodels.jDateField(default=JalaliDate.today)

# Instead of models.DateTimeField → Use jmodels.jDateTimeField
# Instead of models.DateField → Use jmodels.jDateField


# 1404-08-25
today = JalaliDate.today()
# 1404-08-25 19:23:13.311829
now = JalaliDatetime.now()
# 1404-08-25 19:23:13.311870+03:30  
tehran_time = JalaliDatetime.now(TehranTimezone())
# 1404-09-02
next_week = today + timedelta(days=7)
# 1404-09-02 19:23:13.311829   
next_week_dt = now + timedelta(days=7)


# 2025-11-15 18:09:00
g_date_1 = datetime.datetime(2025, 11, 15, 18, 9)
# 1404-08-25 18:09:00.000000
j_date_1 = JalaliDatetime(g_date_1)


# 1404-08-25 00:00:00.000000
j_date_2 = JalaliDatetime(1404, 8, 25)
# 1404-08-25
g_date_2 = j_date_2.date()
# 2025-11-15 00:00:00
g_date_3 = j_date_2.todatetime()


# شنبه, 25 آبان 1404 
alphabet = j_date_2.strftime('%A, %d %B %Y')
# 04/08/25
short_date = j_date_2.strftime('%y/%m/%d')
# 1404-08-25       
numeric_date = j_date_2.strftime('%Y-%m-%d')
# 00:00:00     
time_only = j_date_2.strftime('%H:%M:%S') 
# 1404/08/25 00:00      
full_datetime = j_date_2.strftime('%Y/%m/%d %H:%M')  


# Use jdatetime to parse
# 1404-08-25 00:00:00
j_date_parsed = jdatetime.datetime.strptime(numeric_date, '%Y-%m-%d')
# Convert to khayyam
# 1404-08-25
parsed = JalaliDate(j_date_parsed.year, j_date_parsed.month, j_date_parsed.day)

def parse_jalali(date_str, fmt='%Y-%m-%d'):
    jdt = jdatetime.datetime.strptime(date_str, fmt)
    return JalaliDate(jdt.year, jdt.month, jdt.day)

# 1404-08-25
parsed_2 = parse_jalali('1404-08-25')


# ===================================================================

Arvan_storage = ArvanCloudStorage()


def upload_to(instance, filename):
    file_name, ext = splitext(filename)
    fallback_filename = f"{slugify(file_name, allow_unicode=True).lower()}_{uuid4()}{ext}"

    model_name = instance.__class__.__name__.lower()
    app_name = instance._meta.app_label.lower()

    if model_name == "userprofile":
        user = getattr(instance, "user", None)
        full_name = slugify(user.get_full_name(), allow_unicode=True).lower() if user else "unknown"
        new_filename = f"{user.id}_{full_name}{ext}" if user else fallback_filename
        return f"{app_name}/{model_name}/{new_filename}"

    elif model_name in ["category", "product"]:
        name = getattr(instance, "name", "unknown")
        new_filename = f"{slugify(name, allow_unicode=True).lower()}{ext}"
        return f"{app_name}/{model_name}/{new_filename}"

    elif model_name == "gallery":
        product_name = getattr(instance.product, "name", "unknown") if instance.product else "unknown"
        new_filename = f"{slugify(product_name, allow_unicode=True).lower()}_{uuid4()}{ext}"
        return f"{app_name}/{model_name}/{new_filename}"
    
    elif model_name == "returnrequest":
        order_name = getattr(instance.order, "order_number", "unknown") if instance.order else "unknown"
        new_filename = f"{slugify(order_name, allow_unicode=True).lower()}_{uuid4()}{ext}"
        return f"{app_name}/{model_name}/{new_filename}"

    else:
        return f"others/{fallback_filename}"
    
    
# ===================================================================