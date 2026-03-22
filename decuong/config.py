import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'decuong-secret-key-2024'

    SQLALCHEMY_DATABASE_URI = (
        'mssql+pyodbc://Admin\\SQLEXPRESS/decuong_db'
        '?driver=SQL+Server&trusted_connection=yes'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXTERNAL_API_URL = os.environ.get('EXTERNAL_API_URL') or 'http://localhost:5001'
    EXTERNAL_API_KEY = os.environ.get('EXTERNAL_API_KEY') or 'ext-api-key-123'