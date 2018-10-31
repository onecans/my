import pandas as pd
from django.core.cache import cache
old_read_csv = pd.read_csv

def read_csv(*args, **kwargs):
    pass


