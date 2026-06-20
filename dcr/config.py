import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/registry.db')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    DCR_VERSION = os.getenv('DCR_VERSION', '1.0.0')
    TRACE_STORAGE = 'data/traces/'
    CAPABILITY_STORAGE = 'data/capabilities/'