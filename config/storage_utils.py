from django.core.files.storage import get_storage_class
from django.conf import settings

def get_default_storage():
    return get_storage_class(settings.DEFAULT_FILE_STORAGE)()
