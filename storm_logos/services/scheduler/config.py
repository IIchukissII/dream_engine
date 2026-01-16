"""Scheduler configuration."""

import os

# Database
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'storm_logos_neo4j')

# Email service
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreply@dream-engine.space')

# App settings
BASE_URL = os.getenv('BASE_URL', 'https://chat.dream-engine.space')

# Cleanup settings
DAYS_BEFORE_WARNING = int(os.getenv('DAYS_BEFORE_WARNING', '7'))
HOURS_AFTER_WARNING = int(os.getenv('HOURS_AFTER_WARNING', '24'))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
