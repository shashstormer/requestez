from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from hashlib import md5
import secrets
import string as strings

_ITERABLES = (list, set, tuple)


def choose(arr: _ITERABLES):
    """
    a random object from the passed iterable which is a cryptographically secure choice (i.e. cannot be predicted)
    :param arr:
    :return: a random object from the passed iterable
    """
    return secrets.choice(arr)


def generate_random_string(length) -> str:
    characters = strings.ascii_letters + strings.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string


def aes_enc(key, iv, string) -> str:
    """
        :param key: your 32bytes key
        :param iv: your 16bytes iv
        :param string: string to encode
        :return: encoded string
    """
    cip = AES.new(key, AES.MODE_CBC, iv)
    if type(string) == str:
        string = string.encode("utf-8")
    string = pad(string, cip.block_size)
    string = cip.encrypt(string)
    return base64.b64encode(string).decode('utf-8')


def aes_dec(key, iv, string, decode=True, decoded=False, unpad_data=True) -> str or bytes:
    """
    :param key: your 32bytes key
    :param iv: your 16bytes iv
    :param string: string to decode
    :param decode: return bytes if False otherwise return decoded_data.decode("utf-8")
    :param decoded: has the string been base64 decoded already
    :param unpad_data: wether the data should be unpaded after decryption
    :return: decoded str (or bytes if decode=False)
    """
    cip = AES.new(key, AES.MODE_CBC, iv)
    if not decoded:
        string = base64.b64decode(string)
    try:
        string = cip.decrypt(string)
    except ValueError:
        string = pad(string, cip.block_size)
        string = cip.decrypt(string)
    if unpad_data:
        string = unpad(string, cip.block_size)
    if decode:
        string = string.decode("utf-8")
    return string


def base_64_enc(string) -> str:
    return base64.b64encode(string).decode('utf-8')


def base_64_dec(string, decode_utf_8=False) -> str:
    return base64.b64decode(string) if not decode_utf_8 else base64.b64decode(string).decode('utf-8')


def bytes_to_key(data, salt, output=48) -> bytes:
    assert len(salt) == 8, len(salt)
    data = bytes(data, "utf-8") + salt
    key = md5(data).digest()
    final_key = key
    while len(final_key) < output:
        key = md5(key + data).digest()
        final_key += key
    return final_key[:output]
