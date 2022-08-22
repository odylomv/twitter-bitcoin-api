from stegano import lsbset
from stegano.lsbset import generators


def hide(original_image_path, secret, secret_image_path):
    secret_image = lsbset.hide(original_image_path, secret,
                               generator=generators.eratosthenes(), auto_convert_rgb=True)
    secret_image.save(secret_image_path)


def reveal(image_path):
    return lsbset.reveal(image_path, generator=generators.eratosthenes())
