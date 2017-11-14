## import statements
import requests_oauthlib
import webbrowser
import json
import secret_data # need properly formatted file, see example
from datetime import datetime
import csv

## CACHING SETUP
#--------------------------------------------------
# Caching constants
#--------------------------------------------------

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG = True
CACHE_FNAME = "cache_contents.json"
CREDS_CACHE_FILE = "creds.json"

#--------------------------------------------------
# Load cache files: data and credentials
#--------------------------------------------------
# Load data cache
try:
    with open(CACHE_FNAME, 'r') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except:
    CACHE_DICTION = {}

# Load creds cache
try:
    with open(CREDS_CACHE_FILE,'r') as creds_file:
        cache_creds = creds_file.read()
        CREDS_DICTION = json.loads(cache_creds)
except:
    CREDS_DICTION = {}

#---------------------------------------------
# Cache functions
#---------------------------------------------
def has_cache_expired(timestamp_str, expire_in_days):
    """Check if cache timestamp is over expire_in_days old"""
    # gives current datetime
    now = datetime.now()

    # datetime.strptime converts a formatted string into datetime object
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)

    # subtracting two datetime objects gives you a timedelta object
    delta = now - cache_timestamp
    delta_in_days = delta.days

    # now that we have days as integers, we can just use comparison
    # and decide if cache has expired or not
    if delta_in_days > expire_in_days:
        return True # It's been longer than expiry time
    else:
        return False

def get_from_cache(identifier, dictionary):
    """If unique identifier exists in specified cache dictionary and has not expired
    , return the data associated with it from the request, else return None"""
    identifier = identifier.upper() # Assuming none will differ with case sensitivity here
    if identifier in dictionary:
        data_assoc_dict = dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'],data_assoc_dict["expire_in_days"]):
            if DEBUG:
                print("Cache has expired for {}".format(identifier))
            # also remove old copy from cache
            del dictionary[identifier]
            data = None
        else:
            data = dictionary[identifier]['values']
    else:
        data = None
    return data


def set_in_data_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the data cache dictionary
    , and save the whole dictionary to a file as json"""
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CACHE_FNAME, 'w') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)

def set_in_creds_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the credentials cache dictionary
    , and save the whole dictionary to a file as json"""
    identifier = identifier.upper() # make unique
    CREDS_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CREDS_CACHE_FILE, 'w') as cache_file:
        cache_json = json.dumps(CREDS_DICTION)
        cache_file.write(cache_json)

#####

## ADDITIONAL CODE for program should go here...
## Perhaps authentication setup, functions to get and process data, a class definition... etc.

## OAuth1 API Constants - vary by API
### Private data in a hidden secret_data.py file
CLIENT_KEY = secret_data.client_key # what Tumblr calls Consumer Key
CLIENT_SECRET = secret_data.client_secret # What Tumblr calls Consumer Secret

### Specific to API URLs, not private
REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
BASE_AUTH_URL = "https://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://www.tumblr.com/oauth/access_token"



def get_tokens(client_key=CLIENT_KEY, client_secret=CLIENT_SECRET
    ,request_token_url=REQUEST_TOKEN_URL,base_authorization_url=BASE_AUTH_URL
    ,access_token_url=ACCESS_TOKEN_URL,verifier_auto=True):
    
    oauth_inst = requests_oauthlib.OAuth1Session(client_key,client_secret=client_secret)
    fetch_response = oauth_inst.fetch_request_token(request_token_url)

    # Using the dictionary .get method in these lines
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')

    auth_url = oauth_inst.authorization_url(base_authorization_url)
    # Open the auth url in browser:
    webbrowser.open(auth_url) # For user to interact with & approve access of this app -- this script

    # Deal with required input, which will vary by API
    if verifier_auto: # if the input is default (True), like Twitter
        verifier = input("Please input the verifier:  ")
    else:
        redirect_result = input("Paste the full redirect URL here:  ")
        oauth_resp = oauth_inst.parse_authorization_response(redirect_result) # returns a dictionary -- you may want to inspect that this works and edit accordingly
        verifier = oauth_resp.get('oauth_verifier')

    # Regenerate instance of oauth1session class with more data
    oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret
        , resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret
        , verifier=verifier)

    oauth_tokens = oauth_inst.fetch_access_token(access_token_url) # returns a dictionary

    # Use that dictionary to get these things
    # Tuple assignment syntax
    resource_owner_key, resource_owner_secret = oauth_tokens.get('oauth_token'), oauth_tokens.get('oauth_token_secret')

    return client_key, client_secret, resource_owner_key, resource_owner_secret, verifier

def get_tokens_from_service(service_name_ident, expire_in_days=7): # Default: 7 days for creds expiration
    creds_data = get_from_cache(service_name_ident, CREDS_DICTION)
    if creds_data:
        if DEBUG:
            print("Loading creds from cache...")
            print()
    else:
        if DEBUG:
            print("Fetching fresh credentials...")
            print("Prepare to log in via browser.")
            print()
        creds_data = get_tokens()
        set_in_creds_cache(service_name_ident, creds_data, expire_in_days=expire_in_days)
    return creds_data

def create_request_identifier(url, params_diction):
    sorted_params = sorted(params_diction.items(),key=lambda x:x[0])
    params_str = "_".join([str(e) for l in sorted_params for e in l]) # Make the list of tuples into a flat list using a complex list comprehension
    total_ident = url + "?" + params_str
    return total_ident.upper() # Creating the identifier

def get_data_from_api(request_url,service_ident, params_diction, expire_in_days=7):
    """Check in cache, if not found, load data, save in cache and then return that data"""
    ident = create_request_identifier(request_url, params_diction)
    data = get_from_cache(ident,CACHE_DICTION)
    if data:
        if DEBUG:
            print("Loading from data cache: {}... data".format(ident))
    else:
        if DEBUG:
            print("Fetching new data from {}".format(request_url))

        # Get credentials
        client_key, client_secret, resource_owner_key, resource_owner_secret, verifier = get_tokens_from_service(service_ident)

        # Create a new instance of oauth to make a request with
        oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret
            ,resource_owner_key=resource_owner_key,resource_owner_secret=resource_owner_secret)
        # Call the get method on oauth instance
        # Work of encoding and "signing" the request happens behind the sences, thanks to the OAuth1Session instance in oauth_inst
        resp = oauth_inst.get(request_url,params=params_diction)
        # Get the string data and set it in the cache for next time
        data_str = resp.text
        data = json.loads(data_str)
        set_in_data_cache(ident, data, expire_in_days)
    return data

tumblr_tag_method_url = "https://api.tumblr.com/v2/tagged?"
machine_learning_tag = {"tag":"Machine Learning", "limit":10}
ux_tag = {"tag": "UX", "limit":10}
fieldnames = ["Blog Name", "Blog Type", "Post URL", "Date", "tags"]

def process_api_results(url, params, fieldnames=None, filename=None):
	response = get_data_from_api(url, "Tumblr", params)
	response_records = response["response"]
	actual_rows = [(blah["blog_name"], blah["type"], blah["post_url"], blah["date"], blah["tags"]) for blah in response_records]

	if fieldnames and filename:
		with open(filename+".csv", "w", newline='') as f:
			w = csv.writer(f, delimiter=',', quotechar='"')
			w.writerow(fieldnames)
			for each_rec in actual_rows:
				w.writerow([each_rec[0], each_rec[1], each_rec[2], each_rec[3], ','.join(each_rec[4])])
	else:
		pass
	return actual_rows

process_api_results(tumblr_tag_method_url, machine_learning_tag, fieldnames, "ML_tag_results")
process_api_results(tumblr_tag_method_url, ux_tag, fieldnames, "UX_tag_results")

class Tumblr_response(object):
	""" Only accepts 1 record in type tuple. Processes for ease of testing """
	def __init__(self, obj_tuple):
		self.blog_name = obj_tuple[0]
		self.blog_type = obj_tuple[1]
		self.post_url = obj_tuple[2]
		self.date = obj_tuple[3]
		self.tags = obj_tuple[4]

	def num_tags(self):
		return len(self.tags)

	def __str__(self):
		return "{} | {}".format(self.blog_name, self.blog_type)
## Make sure to run your code and write CSV files by the end of the program.