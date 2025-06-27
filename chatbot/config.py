import os
from dotenv import load_dotenv
load_dotenv()

auth_type = 'Bearer'
consumerID = os.getenv('CONSUMER_ID')
consumerSecret = os.getenv('CONSUMER_SECRET')
url = 'https://fc-data.ssi.com.vn/'
stream_url = 'https://fc-datahub.ssi.com.vn/'