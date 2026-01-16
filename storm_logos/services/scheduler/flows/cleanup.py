"""Account cleanup flow - handles unverified account warnings and deletion."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from neo4j import GraphDatabase
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM,
    BASE_URL, DAYS_BEFORE_WARNING, HOURS_AFTER_WARNING
)

logger = logging.getLogger(__name__)


def get_neo4j_driver():
    """Create Neo4j driver."""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def find_accounts_needing_warning() -> List[Dict[str, Any]]:
    """Find unverified accounts older than threshold that haven't been warned."""
    driver = get_neo4j_driver()
    threshold = datetime.utcnow() - timedelta(days=DAYS_BEFORE_WARNING)

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (u:User)
                WHERE u.email_verified = false
                  AND u.created_at < $threshold
                  AND u.deletion_warning_sent_at IS NULL
                  AND u.email IS NOT NULL
                RETURN u.user_id AS user_id,
                       u.username AS username,
                       u.email AS email,
                       u.created_at AS created_at
            """, threshold=threshold.isoformat())

            users = [dict(record) for record in result]
    finally:
        driver.close()

    logger.info(f"Found {len(users)} accounts needing warning")
    return users


def find_accounts_to_delete() -> List[Dict[str, Any]]:
    """Find accounts warned more than threshold hours ago that are still unverified."""
    driver = get_neo4j_driver()
    threshold = datetime.utcnow() - timedelta(hours=HOURS_AFTER_WARNING)

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (u:User)
                WHERE u.email_verified = false
                  AND u.deletion_warning_sent_at IS NOT NULL
                  AND u.deletion_warning_sent_at < $threshold
                RETURN u.user_id AS user_id,
                       u.username AS username,
                       u.email AS email
            """, threshold=threshold.isoformat())

            users = [dict(record) for record in result]
    finally:
        driver.close()

    logger.info(f"Found {len(users)} accounts to delete")
    return users


def send_warning_email(user: Dict[str, Any]) -> bool:
    """Send account deletion warning email."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured, skipping email")
        return False

    username = user['username']
    email = user['email']
    verify_url = f"{BASE_URL}/auth/verify-email"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #1a1a2e; color: #e0e0e0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #252542; padding: 30px; border-radius: 10px; }}
        h2 {{ color: #e94560; }}
        .warning {{ background: rgba(233, 69, 96, 0.2); padding: 15px; border-radius: 8px; border-left: 4px solid #e94560; }}
        .button {{ display: inline-block; background: #e94560; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
        .footer {{ margin-top: 30px; color: #888; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Account Deletion Warning</h2>
        <p>Hello {username},</p>

        <div class="warning">
            <strong>Your account will be deleted in 24 hours</strong> unless you verify your email address.
        </div>

        <p>We noticed your Dream Engine account hasn't been verified yet. To keep your account active, please verify your email by clicking the button below:</p>

        <a href="{verify_url}" class="button">Verify My Email</a>

        <p>If you no longer wish to use Dream Engine, no action is needed - your account and all associated data will be automatically removed.</p>

        <div class="footer">
            <p>This is an automated message from Dream Engine.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </div>
    </div>
</body>
</html>
"""

    text_body = f"""
Account Deletion Warning

Hello {username},

Your Dream Engine account will be deleted in 24 hours unless you verify your email address.

Verify your email: {verify_url}

If you no longer wish to use Dream Engine, no action is needed.

- Dream Engine Team
"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Action Required: Verify your email within 24 hours'
        msg['From'] = EMAIL_FROM
        msg['To'] = email

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, email, msg.as_string())

        logger.info(f"Warning email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send warning email to {email}: {e}")
        return False


def mark_warning_sent(user_id: str) -> bool:
    """Mark that warning email was sent to user."""
    driver = get_neo4j_driver()
    now = datetime.utcnow().isoformat()

    try:
        with driver.session() as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                SET u.deletion_warning_sent_at = $now
            """, user_id=user_id, now=now)
    finally:
        driver.close()

    logger.info(f"Marked warning sent for user {user_id}")
    return True


def delete_user_account(user: Dict[str, Any]) -> bool:
    """Delete user account and all associated data."""
    driver = get_neo4j_driver()
    user_id = user['user_id']
    username = user['username']

    try:
        with driver.session() as session:
            # Delete all user's data (sessions, dreams, symbols, etc.)
            session.run("""
                MATCH (u:User {user_id: $user_id})
                OPTIONAL MATCH (u)-[:HAS_SESSION]->(s:Session)
                OPTIONAL MATCH (s)-[:HAS_TURN]->(t:Turn)
                OPTIONAL MATCH (s)-[:HAS_SYMBOL]->(sym:SessionSymbol)
                OPTIONAL MATCH (u)-[:HAS_DREAM]->(d:Dream)
                OPTIONAL MATCH (d)-[:HAS_SYMBOL]->(dsym:DreamSymbol)
                DETACH DELETE u, s, t, sym, d, dsym
            """, user_id=user_id)
    finally:
        driver.close()

    logger.info(f"Deleted account for user {username} ({user_id})")
    return True


def account_cleanup_flow() -> Dict[str, int]:
    """Main cleanup flow - warns and deletes unverified accounts."""
    logger.info("Starting account cleanup flow")

    # Step 1: Find and warn accounts
    accounts_to_warn = find_accounts_needing_warning()
    warned_count = 0

    for user in accounts_to_warn:
        try:
            if send_warning_email(user):
                mark_warning_sent(user['user_id'])
                warned_count += 1
            else:
                # Mark as warned even if email failed (to avoid retrying forever)
                mark_warning_sent(user['user_id'])
        except Exception as e:
            logger.error(f"Failed to process warning for {user['username']}: {e}")

    # Step 2: Find and delete expired accounts
    accounts_to_delete = find_accounts_to_delete()
    deleted_count = 0

    for user in accounts_to_delete:
        try:
            if delete_user_account(user):
                deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete account {user['username']}: {e}")

    logger.info(f"Cleanup complete: {warned_count} warned, {deleted_count} deleted")

    return {
        "warned": warned_count,
        "deleted": deleted_count
    }
