import os
import tweepy
import requests
from werkzeug.utils import secure_filename
from secret import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, BEARER_TOKEN
from steganography import reveal, hide

TEMP_IMAGE_PATH = './images/temp.png'
CLEAN_IMAGE_PATH = './images/GitHub.png'

# A Twitter API v1.1 client is needed to upload media
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
image_uploader = tweepy.API(auth)

client = tweepy.Client(
    consumer_key=API_KEY, consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
)


def get_secret(includes):
    url = includes['media'][0].url
    response = requests.get(url)

    with open(TEMP_IMAGE_PATH, 'wb') as file:
        file.write(response.content)
    return reveal(TEMP_IMAGE_PATH)


def post_response(tweet_id, tweet_secret):
    image_path = os.path.join('images/', secure_filename(tweet_id + '.png'))
    hide(CLEAN_IMAGE_PATH, tweet_secret, image_path)

    media = image_uploader.media_upload(image_path)
    client.create_tweet(text='Hi there!', media_ids=[media.media_id], in_reply_to_tweet_id=tweet_id, user_auth=True)


class BitcoinStream(tweepy.StreamingClient):
    def __init__(self, bearer_token):
        super().__init__(bearer_token)
        self.clean_rules()

    def clean_rules(self):
        rule_ids = [rule.id for rule in self.get_rules().data]

        if len(rule_ids) > 0:
            self.delete_rules(rule_ids)
            print('Successfully deleted old rules')
        else:
            print("No rules to delete")

    def on_response(self, response):
        print(response.data.data)
        tweet_secret = get_secret(response.includes)
        post_response(response.data.data['id'], tweet_secret)


streaming_client = BitcoinStream(BEARER_TOKEN)
streaming_client.add_rules(tweepy.StreamRule('#lomvardoBTC has:media -is:reply'))
streaming_client.filter(media_fields=['url'], expansions=['attachments.media_keys'])
