import requests

from steganography import reveal

TEMP_IMAGE_PATH = './images/temp.png'


def get_secret(includes):
    url = includes['media'][0].url
    print(url)
    response = requests.get(url)

    with open(TEMP_IMAGE_PATH, 'wb') as file:
        file.write(response.content)
    return reveal(TEMP_IMAGE_PATH)
