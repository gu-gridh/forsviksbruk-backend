"""
forsviksbruk Settings

Settings configuration for forsviksbruk.
Set DJANGO_ENV=production (in the environment or .env) to load production settings,
otherwise dev settings are used.
"""

import os
from dotenv import load_dotenv

__version__ = '0.1.0'

# Load environment variables from .env file if it exists, before picking the settings
load_dotenv()

if os.getenv('DJANGO_ENV', 'dev').lower() == 'production':
    from .production import *
else:
    from .dev import *
