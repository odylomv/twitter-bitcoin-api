import os
import sqlite3
from urllib.parse import parse_qs, urlparse

import tweepy
from flask import abort, Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

import cat
import encryption as enc
import secret as s
from steganography import hide
from twitter_utils import get_secret

DATABASE = 'db/db.sqlite'
handlers = {}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './images/'
CORS(app)

# A Twitter API v1.1 client is needed to upload media
auth = tweepy.OAuth1UserHandler(s.API_KEY, s.API_SECRET, s.ACCESS_TOKEN, s.ACCESS_TOKEN_SECRET)
image_uploader = tweepy.API(auth)


# Ensure one instance of the db is used
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, isolation_level=None)

    db.row_factory = sqlite3.Row
    return db


# Helper function to query the db
def query_db(query, args=(), one=True):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# Helper function to initialize the database based on a schema
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('db/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# Close db connection on exit
@app.teardown_appcontext
def close_connection(*args):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.errorhandler(404)
def handle_exception(e):
    return jsonify(error=str(e)), 404


@app.route('/twitter_auth')
def twitter_login():
    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=s.CLIENT_ID, client_secret=s.CLIENT_SECRET, redirect_uri=s.REDIRECT_URL,
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

    token = oauth2_user_handler.fetch_token(auth_response)
    response = {'token': token}

    # Get user id to check for keys
    client = tweepy.Client(token['access_token'])
    user_id = client.get_me(user_auth=False).data['id']

    # Generate new keys for first time users
    query = query_db('SELECT * FROM keys WHERE userid=?;', (str(user_id),))
    if query is None:
        keys = enc.generate_rsa_keys()
        query_db('INSERT INTO keys (userid, pubkey, privkey) VALUES(?,?,?);',
                 (str(user_id), keys['public_key'].decode(errors='ignore'),
                  keys['private_key'].decode(errors='ignore')))
        # Send public key to user only the first time
        response['key'] = keys['public_key'].decode()

    return jsonify(response)


@app.route('/twitter_post', methods=['POST'])
def post_stego_tweet():
    access_token = request.form.get('access_token')
    tweet_secret = request.form.get('tweet_secret')
    signature = request.form.get('signature')
    image_method = request.form.get('image_method')
    blockchain = request.form.get('blockchain')

    client = tweepy.Client(access_token)
    user_id = client.get_me(user_auth=False).data['id']

    [verify_key, encryption_key] = query_db('SELECT user_pubkey, pubkey FROM keys WHERE userid=?;', (str(user_id),))
    is_verified = enc.verify_message(tweet_secret, signature, verify_key)

    if is_verified is False:
        return jsonify({'error': 'Invalid Signature'})

    original_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(access_token + '.png'))
    secret_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(access_token + '_secret.png'))

    if image_method == 'local':
        image = request.files.get('tweet_image')

        if '.' not in image.filename and image.filename.rsplit('.', 1)[1].lower() != '.png':
            return '-1'

        image.save(original_path)
    else:
        cat.download_random_cat(original_path)

    encrypted_secret = enc.encrypt_message(tweet_secret + '@' + blockchain, encryption_key).hex()
    print('Encrypted Secret: ' + encrypted_secret)

    hide(original_path, encrypted_secret, secret_path)

    # Give the authorized user permission to tweet the uploaded image
    media = image_uploader.media_upload(secret_path, additional_owners=user_id)
    # Post the stego image with a hashtag
    response = client.create_tweet(text=s.CUSTOM_HASHTAG, media_ids=[media.media_id], user_auth=False)

    return jsonify(response[0])


@app.route('/twitter_search/<tweet_id>', methods=['POST'])
def search_tweet(tweet_id):
    access_token = request.get_json()['access_token']
    client = tweepy.Client(access_token)
    tweet = client.search_recent_tweets('from:' + s.BOT_USERNAME + ' in_reply_to_tweet_id:' + tweet_id,
                                        expansions=['attachments.media_keys'], media_fields=['url'])

    print(tweet.includes)
    try:
        secret = get_secret(tweet.includes)
        print('Encrypted secret: ' + secret)

        user_id = client.get_me(user_auth=False).data['id']
        [key] = query_db('SELECT privkey FROM keys WHERE userid=?;', (str(user_id),))

        decrypted = enc.decrypt_message(bytes.fromhex(secret), key).decode()
        print('Decrypted: ' + decrypted)

        return jsonify({'encrypted_secret': secret, 'secret': decrypted})
    except KeyError:
        abort(404, description='Image not found')


@app.route('/store_pub_key', methods=['POST'])
def store_pub_key():
    access_token = request.get_json()['access_token']
    public_key = request.get_json()['pub_key']

    client = tweepy.Client(access_token)
    user_id = client.get_me(user_auth=False).data['id']

    query_db('UPDATE keys SET user_pubkey=? WHERE userid=?;', (public_key, str(user_id)))
    return {}


if __name__ == '__main__':
    init_db()
    app.run()
