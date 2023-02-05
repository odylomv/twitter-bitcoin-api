import os
import sqlite3

import tweepy
from werkzeug.utils import secure_filename

import cat
import encryption as enc
import secret as s
from btcrpc import send_raw_transaction
from steganography import hide
from twitter_utils import get_secret

CLEAN_IMAGE_PATH = './images/temp_clean.png'
DATABASE = 'db/db.sqlite'

# A Twitter API v1.1 client is needed to upload media
auth = tweepy.OAuth1UserHandler(s.API_KEY, s.API_SECRET, s.ACCESS_TOKEN, s.ACCESS_TOKEN_SECRET)
image_uploader = tweepy.API(auth)

client = tweepy.Client(
    consumer_key=s.API_KEY, consumer_secret=s.API_SECRET,
    access_token=s.ACCESS_TOKEN, access_token_secret=s.ACCESS_TOKEN_SECRET
)

db = sqlite3.connect(DATABASE, isolation_level=None)


# Helper function to query the db
def query_db(query, args=(), one=True):
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def post_response(tweet_id, tweet_secret):
    cat.download_random_cat(CLEAN_IMAGE_PATH)
    # print('Cat downloaded')
    image_path = os.path.join('./images/', secure_filename(tweet_id + '.png'))
    if tweet_secret is None:
        hide(CLEAN_IMAGE_PATH, 'NONE', image_path)
    else:
        hide(CLEAN_IMAGE_PATH, tweet_secret, image_path)

    # print('Secret hidden')

    # Upload the stego image and give ownership to the user
    user_id = client.get_me().data['id']
    media = image_uploader.media_upload(image_path, additional_owners=user_id)
    print('Media upload complete. Posting reply...')
    client.create_tweet(text='Hi there!', media_ids=[media.media_id], in_reply_to_tweet_id=tweet_id)
    print('Reply posted')


class BitcoinStream(tweepy.StreamingClient):
    def __init__(self, bearer_token):
        super().__init__(bearer_token)
        print('Initiating streaming client...')
        self.clean_rules()
        print('Initialization successful')

    # Clear previous rules on init
    def clean_rules(self):
        rule_ids = [rule.id for rule in self.get_rules().data]

        if len(rule_ids) > 0:
            self.delete_rules(rule_ids)
            print('Successfully deleted old rules')
        else:
            print("No rules to delete")

    def on_response(self, response):
        # print(response.data.data)
        tweet_secret = get_secret(response.includes)

        # Get user key pair from db
        user_id = response.data.data['author_id']
        [pub_key, private_key] = query_db('SELECT pubkey, privkey FROM keys WHERE userid=?;', (str(user_id),))

        # Run the bitcoin transaction
        decrypted = enc.decrypt_message(bytes.fromhex(tweet_secret), private_key).decode()
        [signed_tx, blockchain] = decrypted.split('@')
        result = send_raw_transaction(signed_tx)
        print('Transaction output: ' + result)

        # Encrypt CLI output and post as a reply
        encrypted = enc.encrypt_message(result, pub_key).hex()
        print('Posting...')
        post_response(response.data.data['id'], encrypted)
        print('Post completed')


streaming_client = BitcoinStream(s.BEARER_TOKEN)
# Only filter top-level tweets with the right hashtag
streaming_client.add_rules(tweepy.StreamRule(s.CUSTOM_HASHTAG + ' has:media -is:reply'))
# Start filtering and return the user ID and the image for each match
streaming_client.filter(tweet_fields=['author_id'], media_fields=['url'], expansions=['attachments.media_keys'])
