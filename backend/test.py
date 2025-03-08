
import hmac
import time
import hashlib
def totp(secret: str, timestamp: int):
    time_now = time.time()
    time_elapsed = int(time_now - timestamp)
    TOTP_DIGITS = 6
    TIME_STEP = 30
    time_counter = int(time_elapsed / TIME_STEP)
    counter = [None] * 8

    # convert to 8 byte array
    for i in range(7, -1, -1):
        counter[i] = time_counter & 0xFF
        time_counter >>= 8

    h = hmac.new(bytes(secret.encode()), bytes(counter), hashlib.sha1)
    hmac_digest = h.digest()
    offset = hmac_digest[19] & 0x0F
    bin_code = ((hmac_digest[offset] & 0x7F) << 24 |
                ((hmac_digest[offset + 1] & 0xFF) << 16) |
                ((hmac_digest[offset + 2] & 0xFF) << 8) |
                (hmac_digest[offset + 3] & 0xFF))
    
    mod_divisor = 1
    for i in range(TOTP_DIGITS):
        mod_divisor *= 10
    totp_code = bin_code % mod_divisor
    return totp_code