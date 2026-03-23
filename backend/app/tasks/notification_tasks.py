"""Notification-related async tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger("social_media.tasks.notifications")


@celery_app.task(name="app.tasks.notification_tasks.send_push_notification")
def send_push_notification(user_id: str, title: str, body: str, data: dict = None) -> dict:
    """Send a push notification to a user's devices."""
    logger.info(f"Sending push notification to user {user_id}: {title}")
    try:
        # In production, integrate with FCM, APNs, or similar push service
        logger.info(f"Push notification sent to user {user_id}")
        return {"user_id": user_id, "status": "sent"}
    except Exception as e:
        logger.error(f"Failed to send push notification to {user_id}: {e}")
        return {"user_id": user_id, "status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.notification_tasks.send_email_notification")
def send_email_notification(email: str, subject: str, body: str) -> dict:
    """Send an email notification."""
    logger.info(f"Sending email notification to {email}: {subject}")
    try:
        import smtplib
        from email.mime.text import MIMEText
        from app.config import settings

        if settings.SMTP_HOST and settings.SMTP_HOST != "localhost":
            msg = MIMEText(body, "html")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = email

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

        logger.info(f"Email notification sent to {email}")
        return {"email": email, "status": "sent"}
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}")
        return {"email": email, "status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.notification_tasks.batch_send_notifications")
def batch_send_notifications(notification_data: list[dict]) -> dict:
    """Send multiple notifications in batch."""
    logger.info(f"Batch sending {len(notification_data)} notifications")
    sent = 0
    failed = 0
    for data in notification_data:
        try:
            send_push_notification.delay(
                data["user_id"], data["title"], data.get("body", ""), data.get("data")
            )
            sent += 1
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(notification_data)}


@celery_app.task(name="app.tasks.notification_tasks.send_follow_notification")
def send_follow_notification(follower_id: str, follower_username: str, target_id: str) -> dict:
    """Send a follow notification."""
    logger.info(f"User {follower_username} followed {target_id}")
    return send_push_notification(
        target_id,
        "New Follower",
        f"@{follower_username} started following you",
        {"type": "follow", "user_id": follower_id},
    )


@celery_app.task(name="app.tasks.notification_tasks.send_like_notification")
def send_like_notification(liker_id: str, liker_username: str, post_id: str, post_author_id: str) -> dict:
    """Send a like notification."""
    if liker_id == post_author_id:
        return {"status": "skipped", "reason": "self_like"}
    logger.info(f"User {liker_username} liked post {post_id}")
    return send_push_notification(
        post_author_id,
        "New Like",
        f"@{liker_username} liked your post",
        {"type": "like", "post_id": post_id, "user_id": liker_id},
    )


@celery_app.task(name="app.tasks.notification_tasks.send_comment_notification")
def send_comment_notification(
    commenter_id: str, commenter_username: str, post_id: str, post_author_id: str, comment_preview: str
) -> dict:
    """Send a comment notification."""
    if commenter_id == post_author_id:
        return {"status": "skipped", "reason": "self_comment"}
    logger.info(f"User {commenter_username} commented on post {post_id}")
    return send_push_notification(
        post_author_id,
        "New Comment",
        f"@{commenter_username}: {comment_preview[:100]}",
        {"type": "comment", "post_id": post_id, "user_id": commenter_id},
    )
