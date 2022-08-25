import requests

import secret as s


def get_random_cat():
    headers = {'x-api-key': s.CAT_API_KEY}
    response = requests.get('https://api.thecatapi.com/v1/images/search?mime_types=png', headers)

    return response.json()[0]


def download_random_cat(path):
    image = requests.get(get_random_cat()['url'])
    with open(path, 'wb') as file:
        file.write(image.content)
