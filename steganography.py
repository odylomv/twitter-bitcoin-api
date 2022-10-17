import os

from PIL import Image
from stegano import lsb


def check_image(path):
    print(path)
    img = Image.open(path)
    print(img.info.get('transparency'))
    print(img.mode)


def shrink_big_images(path):
    if os.path.getsize(path) > 768000:  # 750KB
        img = Image.open(path)
        ratio = min(512 / img.width, 512 / img.height)
        img.thumbnail((int(img.width * ratio), int(img.height * ratio)), Image.ANTIALIAS)
        img.save(path)


def convert_image(path):
    png = Image.open(path)
    if png.mode == 'RGBA':
        png.load()  # required for png.split()

        background = Image.new("RGB", png.size, (255, 255, 255))
        background.paste(png, mask=png.getchannel('A'))
        path = './images/edited.png'
        background.save(path, 'PNG')

    shrink_big_images(path)
    return path


def hide(original_image_path, secret, secret_image_path):
    print('Hiding...')
    check_image(original_image_path)
    secret_image = lsb.hide(convert_image(original_image_path), secret, auto_convert_rgb=True)
    secret_image.save(secret_image_path)
    check_image(secret_image_path)


def reveal(image_path):
    print('Revealing...')
    check_image(image_path)
    return lsb.reveal(image_path)
