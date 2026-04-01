import random
import string

def generate_shop_code(length: int = 6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))