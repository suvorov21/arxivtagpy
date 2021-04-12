"""Wsgi wrapper for the app."""

from app import app_init

app = app_init()

if __name__ == "__main__":
    if app:
        app.run()
