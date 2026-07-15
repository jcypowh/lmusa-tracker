import os
import uuid
from functools import wraps

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from sqlalchemy import text
from werkzeug.utils import secure_filename

import config
from colors import mix_with_white, readable_text_color
from models import (
    ROLE_LABELS,
    ROLES,
    Comment,
    ImprovementArea,
    KnowledgeNote,
    Piece,
    Video,
    db,
)

PIECE_COLOR_PALETTE = [
    "#4f46e5", "#059669", "#dc2626", "#d97706", "#0891b2", "#7c3aed", "#be185d",
]

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{config.DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

db.init_app(app)
app.jinja_env.globals["mix_with_white"] = mix_with_white
app.jinja_env.globals["readable_text_color"] = readable_text_color

os.makedirs(config.UPLOAD_DIR, exist_ok=True)

# Default neat-grid card layout (client-side "Tidy up" recomputes this against
# the actual viewport width; these are just sane server-side defaults for a
# freshly created card before any dragging happens).
GRID_MARGIN = 16
GRID_CARD_W = 170
GRID_CARD_H = 116
GRID_GAP = 14
GRID_COLS = 2


@app.context_processor
def inject_globals():
    return {
        "current_role": session.get("role"),
        "role_labels": ROLE_LABELS,
    }


def require_role(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("role"):
            return redirect(url_for("choose_role"))
        return view(*args, **kwargs)

    return wrapped


def next_palette_color():
    count = Piece.query.count()
    return PIECE_COLOR_PALETTE[count % len(PIECE_COLOR_PALETTE)]


def allowed_video(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in config.ALLOWED_VIDEO_EXTENSIONS


def save_video(file_storage, piece_id, area_id=None, is_reference=False):
    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[-1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(config.UPLOAD_DIR, stored_name))
    video = Video(
        piece_id=piece_id,
        area_id=area_id,
        filename=stored_name,
        original_filename=original,
        uploaded_by=session.get("role"),
        is_reference=is_reference,
    )
    db.session.add(video)
    return video


def delete_video_file(video):
    try:
        os.remove(os.path.join(config.UPLOAD_DIR, video.filename))
    except OSError:
        pass


# --- Role selection -------------------------------------------------------


@app.route("/")
def index():
    if session.get("role"):
        return redirect(url_for("list_pieces"))
    return redirect(url_for("choose_role"))


@app.route("/who-are-you")
def choose_role():
    return render_template("choose_role.html", roles=ROLES)


@app.route("/set-role", methods=["POST"])
def set_role():
    role = request.form.get("role")
    if role not in ROLES:
        abort(400)
    session["role"] = role
    return redirect(url_for("list_pieces"))


@app.route("/switch-role")
def switch_role():
    session.pop("role", None)
    return redirect(url_for("choose_role"))


# --- Pieces ----------------------------------------------------------------


@app.route("/pieces")
@require_role
def list_pieces():
    pieces = Piece.query.order_by(Piece.created_at).all()
    return render_template("pieces.html", pieces=pieces, next_color=next_palette_color())


@app.route("/pieces/add", methods=["POST"])
@require_role
def add_piece():
    title = request.form.get("title", "").strip()
    composer = request.form.get("composer", "").strip()
    color = request.form.get("color", "").strip()
    if title:
        piece = Piece(title=title, composer=composer)
        if color.startswith("#") and len(color) == 7:
            piece.color = color
        db.session.add(piece)
        db.session.commit()
    return redirect(url_for("list_pieces"))


@app.route("/pieces/<int:piece_id>")
@require_role
def piece_detail(piece_id):
    piece = Piece.query.get_or_404(piece_id)
    return render_template("piece_detail.html", piece=piece)


@app.route("/pieces/<int:piece_id>/color", methods=["POST"])
@require_role
def update_piece_color(piece_id):
    piece = Piece.query.get_or_404(piece_id)
    color = request.form.get("color", "").strip()
    if color.startswith("#") and len(color) == 7:
        piece.color = color
        db.session.commit()
    return redirect(url_for("piece_detail", piece_id=piece.id))


@app.route("/pieces/<int:piece_id>/knowledge/add", methods=["POST"])
@require_role
def add_knowledge_note(piece_id):
    piece = Piece.query.get_or_404(piece_id)
    body = request.form.get("body", "").strip()
    if body:
        db.session.add(
            KnowledgeNote(piece_id=piece.id, author=session.get("role"), body=body)
        )
        db.session.commit()
    return redirect(url_for("piece_detail", piece_id=piece.id))


@app.route("/knowledge/<int:note_id>/delete", methods=["POST"])
@require_role
def delete_knowledge_note(note_id):
    note = KnowledgeNote.query.get_or_404(note_id)
    piece_id = note.piece_id
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("piece_detail", piece_id=piece_id))


@app.route("/pieces/<int:piece_id>/areas/add", methods=["POST"])
@require_role
def add_area(piece_id):
    piece = Piece.query.get_or_404(piece_id)
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    if title:
        active = [a for a in piece.areas if not a.archived]
        slot = len(active)
        col = slot % GRID_COLS
        row = slot // GRID_COLS
        area = ImprovementArea(
            piece_id=piece.id,
            title=title,
            description=description,
            status="orange",
            created_by=session.get("role"),
            pos_x=GRID_MARGIN + col * (GRID_CARD_W + GRID_GAP),
            pos_y=GRID_MARGIN + row * (GRID_CARD_H + GRID_GAP),
            z_index=slot,
        )
        db.session.add(area)
        db.session.commit()
    return redirect(url_for("piece_detail", piece_id=piece.id))


@app.route("/pieces/<int:piece_id>/tidy", methods=["POST"])
@require_role
def tidy_board(piece_id):
    piece = Piece.query.get_or_404(piece_id)
    data = request.get_json(silent=True) or {}
    positions = data.get("positions") or []
    by_id = {a.id: a for a in piece.areas}
    for i, entry in enumerate(positions):
        area = by_id.get(entry.get("id"))
        if not area:
            continue
        try:
            area.pos_x = max(0, min(int(entry["x"]), 4000))
            area.pos_y = max(0, min(int(entry["y"]), 4000))
        except (KeyError, TypeError, ValueError):
            continue
        area.z_index = i
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/areas/<int:area_id>/position", methods=["POST"])
@require_role
def update_position(area_id):
    area = ImprovementArea.query.get_or_404(area_id)
    data = request.get_json(silent=True) or {}
    try:
        x = int(data["x"])
        y = int(data["y"])
    except (KeyError, TypeError, ValueError):
        abort(400)
    area.pos_x = max(0, min(x, 4000))
    area.pos_y = max(0, min(y, 4000))
    top_z = db.session.query(db.func.max(ImprovementArea.z_index)).filter_by(
        piece_id=area.piece_id
    ).scalar() or 0
    area.z_index = top_z + 1
    db.session.commit()
    return jsonify({"ok": True, "z_index": area.z_index})


@app.route("/pieces/<int:piece_id>/videos/upload", methods=["POST"])
@require_role
def upload_piece_video(piece_id):
    piece = Piece.query.get_or_404(piece_id)
    file_storage = request.files.get("video")
    if file_storage and file_storage.filename and allowed_video(file_storage.filename):
        video = save_video(file_storage, piece.id)
        video.note = request.form.get("note", "").strip()
        db.session.commit()
    return redirect(url_for("piece_detail", piece_id=piece.id))


@app.route("/pieces/<int:piece_id>/reference/upload", methods=["POST"])
@require_role
def upload_reference_video(piece_id):
    piece = Piece.query.get_or_404(piece_id)
    file_storage = request.files.get("video")
    if file_storage and file_storage.filename and allowed_video(file_storage.filename):
        Video.query.filter_by(piece_id=piece.id, is_reference=True).update(
            {"is_reference": False}
        )
        video = save_video(file_storage, piece.id, is_reference=True)
        video.note = request.form.get("note", "").strip()
        db.session.commit()
    return redirect(url_for("piece_detail", piece_id=piece.id))


@app.route("/videos/<int:video_id>/delete", methods=["POST"])
@require_role
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)
    piece_id = video.piece_id
    delete_video_file(video)
    db.session.delete(video)
    db.session.commit()
    next_url = request.form.get("next") or url_for("piece_detail", piece_id=piece_id)
    return redirect(next_url)


# --- Improvement areas -------------------------------------------------------


@app.route("/areas/<int:area_id>")
@require_role
def area_detail(area_id):
    area = ImprovementArea.query.get_or_404(area_id)
    return render_template("area_detail.html", area=area)


@app.route("/areas/<int:area_id>/percent", methods=["POST"])
@require_role
def update_percent(area_id):
    if session.get("role") != "darren":
        abort(403)
    area = ImprovementArea.query.get_or_404(area_id)
    data = request.get_json(silent=True) or {}
    try:
        percent = int(data["percent"])
    except (KeyError, TypeError, ValueError):
        abort(400)
    area.percent = max(0, min(100, percent))
    db.session.commit()
    return jsonify({"ok": True, "percent": area.percent})


@app.route("/areas/<int:area_id>/archive", methods=["POST"])
@require_role
def archive_area(area_id):
    area = ImprovementArea.query.get_or_404(area_id)
    area.archived = True
    db.session.commit()
    return redirect(url_for("piece_detail", piece_id=area.piece_id))


@app.route("/areas/<int:area_id>/unarchive", methods=["POST"])
@require_role
def unarchive_area(area_id):
    area = ImprovementArea.query.get_or_404(area_id)
    area.archived = False
    db.session.commit()
    return redirect(url_for("piece_detail", piece_id=area.piece_id))


@app.route("/areas/<int:area_id>/delete", methods=["POST"])
@require_role
def delete_area(area_id):
    if session.get("role") != "darren":
        abort(403)
    area = ImprovementArea.query.get_or_404(area_id)
    piece_id = area.piece_id
    db.session.delete(area)
    db.session.commit()
    return redirect(url_for("piece_detail", piece_id=piece_id))


@app.route("/areas/<int:area_id>/comments/add", methods=["POST"])
@require_role
def add_comment(area_id):
    area = ImprovementArea.query.get_or_404(area_id)
    body = request.form.get("body", "").strip()
    video_id = request.form.get("video_id") or None
    timestamp = request.form.get("timestamp_seconds") or None
    if body:
        comment = Comment(
            area_id=area.id,
            video_id=int(video_id) if video_id else None,
            timestamp_seconds=int(timestamp) if timestamp else None,
            author=session.get("role"),
            body=body,
        )
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for("area_detail", area_id=area.id))


@app.route("/areas/<int:area_id>/videos/upload", methods=["POST"])
@require_role
def upload_area_video(area_id):
    area = ImprovementArea.query.get_or_404(area_id)
    file_storage = request.files.get("video")
    if file_storage and file_storage.filename and allowed_video(file_storage.filename):
        video = save_video(file_storage, area.piece_id, area_id=area.id)
        video.note = request.form.get("note", "").strip()
        db.session.commit()
    return redirect(url_for("area_detail", area_id=area.id))


# --- Serving uploaded videos -------------------------------------------------


@app.route("/uploads/<path:filename>")
@require_role
def uploaded_file(filename):
    return send_from_directory(config.UPLOAD_DIR, filename)


def seed_data():
    if Piece.query.first() is None:
        db.session.add(
            Piece(
                title="Prelude in G minor, Op. 23 No. 5",
                composer="Rachmaninoff",
                color="#7c3aed",
            )
        )
        db.session.commit()


def ensure_schema():
    """Lightweight inline migration: add newer columns to an existing sqlite db."""
    with db.engine.connect() as conn:
        area_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(improvement_area)"))}
        for col, ddl in [
            ("pos_x", "ALTER TABLE improvement_area ADD COLUMN pos_x INTEGER DEFAULT 16"),
            ("pos_y", "ALTER TABLE improvement_area ADD COLUMN pos_y INTEGER DEFAULT 16"),
            ("z_index", "ALTER TABLE improvement_area ADD COLUMN z_index INTEGER DEFAULT 0"),
            ("archived", "ALTER TABLE improvement_area ADD COLUMN archived BOOLEAN DEFAULT 0"),
            ("percent", "ALTER TABLE improvement_area ADD COLUMN percent INTEGER DEFAULT 0"),
        ]:
            if col not in area_cols:
                conn.execute(text(ddl))

        piece_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(piece)"))}
        if "color" not in piece_cols:
            conn.execute(
                text("ALTER TABLE piece ADD COLUMN color VARCHAR(7) DEFAULT '#4f46e5'")
            )

        video_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(video)"))}
        if "is_reference" not in video_cols:
            conn.execute(
                text("ALTER TABLE video ADD COLUMN is_reference BOOLEAN DEFAULT 0")
            )
        conn.commit()


with app.app_context():
    db.create_all()
    ensure_schema()
    seed_data()


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5011)))
