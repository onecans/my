from django.conf import settings
from django.utils.module_loading import import_string

def get_backend():
    backend_class = import_string(settings.DATA_READER_BACKEND)
    return backend_class()


backend = get_backend()
