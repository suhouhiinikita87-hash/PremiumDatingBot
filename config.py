import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PRICE_MONTH = int(os.getenv("PRICE_MONTH"))
PRICE_VIEW_LIKES = int(os.getenv("PRICE_VIEW_LIKES"))