from config.storages import ArvanCloudStorage
from os.path import splitext
from uuid import uuid4
from django.utils.text import slugify



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

    else:
        return f"others/{fallback_filename}"