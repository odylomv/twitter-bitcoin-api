import os
import tweepy
from urllib.parse import urlparse, parse_qs
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from secret import API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CLIENT_ID, CLIENT_SECRET, REDIRECT_URL
from steganography import hide

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'images/'
CORS(app)
handlers = dict()
# A Twitter API v1.1 client is needed to upload media
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
image_uploader = tweepy.API(auth)


@app.route('/twitter_auth')
def twitter_login():
    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URL,
        scope=['tweet.read', 'tweet.write', 'users.read']
    )
    response = jsonify(oauth2_user_handler.get_authorization_url())
    # Save the handler in a dict with the state as key
    queries = str(urlparse(response.get_json()).query)
    handlers[parse_qs(queries)['state'][0]] = oauth2_user_handler

    return response


@app.route('/twitter_token', methods=['POST'])
def twitter_get_access_token():
    auth_response = request.get_json()['url']
    # Get the correct handler based on the state value
    queries = str(urlparse(auth_response).query)
    oauth2_user_handler = handlers[parse_qs(queries)['state'][0]]

    response = jsonify(oauth2_user_handler.fetch_token(auth_response))
    return response


@app.route('/twitter_post', methods=['POST'])
def post_stego_tweet():
    access_token = request.form.get('access_token')
    tweet_secret = request.form.get('tweet_secret')
    image = request.files.get('tweet_image')

    if '.' not in image.filename and image.filename.rsplit('.', 1)[1].lower() != '.png':
        return '-1'

    original_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(access_token + '.png'))
    secret_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(access_token + '_secret.png'))
    image.save(original_path)
    hide(original_path, tweet_secret, secret_path)

    client = tweepy.Client(access_token)
    user_id = client.get_me(user_auth=False).data['id']
    # Give the authorized user permission to tweet the uploaded image
    media = image_uploader.media_upload(secret_path, additional_owners=user_id)
    # Post the stego image with a hashtag
    client.create_tweet(text='#lomvardoBTC', media_ids=[media.media_id], user_auth=False)

    return '200'


if __name__ == '__main__':
    app.run()
