from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limit keys are based on the client IP address.
# This can be swapped to get_remote_address or a user-id based key function.
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
