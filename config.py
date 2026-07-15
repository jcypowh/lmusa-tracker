import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "lmusa.db"))
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# iPhone video recordings can be large; allow up to 1GB per upload.
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024

ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "m4v", "avi", "webm"}
