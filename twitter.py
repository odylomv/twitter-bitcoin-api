import os

import tweepy
from werkzeug.utils import secure_filename

import cat
import secret as s
from steganography import hide
from twitter_utils import get_secret

CLEAN_IMAGE_PATH = './images/temp_clean.png'

# A Twitter API v1.1 client is needed to upload media
auth = tweepy.OAuth1UserHandler(s.API_KEY, s.API_SECRET, s.ACCESS_TOKEN, s.ACCESS_TOKEN_SECRET)
image_uploader = tweepy.API(auth)

client = tweepy.Client(
    consumer_key=s.API_KEY, consumer_secret=s.API_SECRET,
    access_token=s.ACCESS_TOKEN, access_token_secret=s.ACCESS_TOKEN_SECRET
)


def post_response(tweet_id, tweet_secret):
    cat.download_random_cat(CLEAN_IMAGE_PATH)
    print('Cat downloaded')
    image_path = os.path.join('./images/', secure_filename(tweet_id + '.png'))
    if tweet_secret is None:
        hide(CLEAN_IMAGE_PATH, 'NONE', image_path)
    else:
        hide(CLEAN_IMAGE_PATH, tweet_secret + '-response', image_path)


    print('Secret hidden')

    user_id = client.get_me().data['id']
    media = image_uploader.media_upload(image_path, additional_owners=user_id)
    print('Starting upload...')
    client.create_tweet(text='Hi there!', media_ids=[media.media_id], in_reply_to_tweet_id=tweet_id)


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
        print('Posting...')
        post_response(response.data.data['id'], tweet_secret)


streaming_client = BitcoinStream(s.BEARER_TOKEN)
streaming_client.add_rules(tweepy.StreamRule(s.CUSTOM_HASHTAG + ' has:media -is:reply'))
streaming_client.filter(media_fields=['url'], expansions=['attachments.media_keys'])
