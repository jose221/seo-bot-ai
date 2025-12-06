import binascii
import hashlib
import base64


def encode_key(texto: str) -> str:
    texto_bytes = texto.encode('utf-8')
    hash_obj = hashlib.sha256(texto_bytes)
    texto_hexadecimal = binascii.hexlify(texto_bytes).decode('utf-8')
    return hash_obj.hexdigest()


def decode_key(hexadecimal: str) -> str:
    hexadecimal_bytes = binascii.unhexlify(hexadecimal.encode('utf-8'))
    texto = hexadecimal_bytes.decode('utf-8')
    return texto


# Function to encode text to base64
def encode_to_base64_key(text):
    # Convert the text to bytes, encode to base64, and return the encoded string
    text_bytes = text.encode('utf-8')
    base64_bytes = base64.b64encode(text_bytes)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string


# Function to decode base64 to text
def decode_from_base64_key(base64_string):
    # Convert the base64 string to bytes, decode it, and return the original text
    base64_bytes = base64_string.encode('utf-8')
    text_bytes = base64.b64decode(base64_bytes)
    text = text_bytes.decode('utf-8')
    return text
