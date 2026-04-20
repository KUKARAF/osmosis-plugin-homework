async def handle_request_homework_photo(user, db, subject: str, message: str, **_) -> dict:
    """Tool handler for request_homework_photo.

    Returns a dict that the frontend detects to render the photo capture widget.
    """
    return {
        "action": "capture_homework_photo",
        "subject": subject,
        "message": message,
        "upload_url": "/api/plugins/homework/analyze",
    }
