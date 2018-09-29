def is_sort(s):
    x = round(s[0], 2)
    for k, v in s.items():
        if round(v, 2) < x:
            x = round(v, 2)
            print(False, k, v)

            return False
    return True


for key in db.iterator(include_value=False):
    if not key.decode().endswith('shares'):
        continue

    s = pickle.loads(zlib.decompress(db.get(key)))
    if not is_sort(s):
        print(key)
for key in db.iterator(include_value=False):
    if not key.decode().endswith('liquidity'):
        continue

    s = pickle.loads(zlib.decompress(db.get(key)))
    if not is_sort(s):
        print(key)
history
