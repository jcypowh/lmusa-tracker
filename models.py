from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

STATUS_CHOICES = ["green", "orange", "blue"]
STATUS_LABELS = {"green": "Good", "orange": "Working On", "blue": "Problematic"}

ROLES = ["darren", "jeremy"]
ROLE_LABELS = {"darren": "Darren (Teacher)", "jeremy": "Jeremy (Student)"}


class Piece(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    composer = db.Column(db.String(200))
    color = db.Column(db.String(7), default="#4f46e5", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    areas = db.relationship(
        "ImprovementArea",
        backref="piece",
        cascade="all, delete-orphan",
        order_by="ImprovementArea.created_at",
    )
    videos = db.relationship(
        "Video",
        backref="piece",
        cascade="all, delete-orphan",
        order_by="Video.created_at.desc()",
    )
    knowledge_notes = db.relationship(
        "KnowledgeNote",
        backref="piece",
        cascade="all, delete-orphan",
        order_by="KnowledgeNote.created_at",
    )

    def average_percent(self):
        if not self.areas:
            return 0
        return round(sum(a.percent for a in self.areas) / len(self.areas))


class ImprovementArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    piece_id = db.Column(db.Integer, db.ForeignKey("piece.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(10), default="orange", nullable=False)
    percent = db.Column(db.Integer, default=0, nullable=False)
    created_by = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pos_x = db.Column(db.Integer, default=16)
    pos_y = db.Column(db.Integer, default=16)
    z_index = db.Column(db.Integer, default=0)
    archived = db.Column(db.Boolean, default=False, nullable=False)

    comments = db.relationship(
        "Comment",
        backref="area",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )
    videos = db.relationship(
        "Video", backref="area", order_by="Video.created_at.desc()"
    )


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    piece_id = db.Column(db.Integer, db.ForeignKey("piece.id"), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey("improvement_area.id"), nullable=True)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300))
    uploaded_by = db.Column(db.String(10))
    note = db.Column(db.Text)
    is_reference = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class KnowledgeNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    piece_id = db.Column(db.Integer, db.ForeignKey("piece.id"), nullable=False)
    author = db.Column(db.String(10), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(db.Integer, db.ForeignKey("improvement_area.id"), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=True)
    timestamp_seconds = db.Column(db.Integer, nullable=True)
    author = db.Column(db.String(10), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    video = db.relationship("Video")
