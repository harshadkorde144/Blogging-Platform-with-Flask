from datetime import datetime, timezone

import bleach


def reading_time(html):
    """Estimated minutes to read (200 words/min)."""
    words = len(bleach.clean(html or "", tags=[], strip=True).split())
    return max(1, round(words / 200))


def timeago(dt):
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    seconds = int((datetime.now(timezone.utc) - dt).total_seconds())
    if seconds < 60:
        return "just now"
    for unit, size in (("year", 31536000), ("month", 2592000), ("day", 86400),
                       ("hour", 3600), ("minute", 60)):
        if seconds >= size:
            value = seconds // size
            return f"{value} {unit}{'s' if value > 1 else ''} ago"
    return "just now"


def avatar_color(name):
    hue = (sum(ord(c) for c in name or "?") * 37) % 360
    return f"hsl({hue}, 55%, 42%)"


def register_filters(app):
    app.jinja_env.filters.update(reading_time=reading_time, timeago=timeago,
                                 avatar_color=avatar_color)
