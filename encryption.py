from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


def generate_rsa_keys():
    # Generate a new 4096-bit RSA key pair
    key = RSA.generate(4096)
    # Return a dict containing the key pair
    return {
        'private_key': key.exportKey('PEM'),
        'public_key': key.publickey().exportKey('PEM')
    }


def encrypt_message(message: str, key):
    cipher = PKCS1_OAEP.new(RSA.importKey(key))
    return cipher.encrypt(message.encode('utf-8'))


def decrypt_message(encrypted_message, key):
    cipher = PKCS1_OAEP.new(RSA.importKey(key))
    return cipher.decrypt(encrypted_message)


def verify_message(message, signature, key):
    # print("Verify:")
    try:
        sha_hash = SHA256.new(message.encode('utf-8'))
        # print(sha_hash.hexdigest())
        pkcs1_15.new(RSA.importKey(key)).verify(sha_hash, bytes.fromhex(signature))

        return True
    except (ValueError, TypeError) as e:
        print('Verification failed: ' + e)
        return False
