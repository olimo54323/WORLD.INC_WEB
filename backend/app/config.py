import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'world-inc-super-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///worldinc.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'worldinc:'
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries

class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific settings here

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}