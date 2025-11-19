import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Beat, Purchase
from PIL import Image
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///beatstore.db'
app.config['UPLOAD_FOLDER'] = 'static/audio'
app.config['IMAGE_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS


def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@app.route('/')
def index():
    recent_beats = Beat.query.order_by(Beat.created_at.desc()).limit(8).all()
    return render_template('index.html', beats=recent_beats)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    user_beats = Beat.query.filter_by(user_id=current_user.id).all()
    purchased_beats = Purchase.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', beats=user_beats, purchases=purchased_beats)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        bpm = int(request.form['bpm'])
        genre = request.form['genre']

        # Handle audio file
        if 'audio_file' not in request.files:
            flash('No audio file selected')
            return redirect(request.url)

        audio_file = request.files['audio_file']
        if audio_file.filename == '':
            flash('No audio file selected')
            return redirect(request.url)

        if audio_file and allowed_audio_file(audio_file.filename):
            audio_filename = str(uuid.uuid4()) + '_' + secure_filename(audio_file.filename)
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
            audio_file.save(audio_path)
        else:
            flash('Invalid audio file format')
            return redirect(request.url)

        # Handle cover image
        cover_filename = None
        if 'cover_image' in request.files:
            cover_image = request.files['cover_image']
            if cover_image and cover_image.filename != '' and allowed_image_file(cover_image.filename):
                cover_filename = str(uuid.uuid4()) + '_' + secure_filename(cover_image.filename)
                cover_path = os.path.join(app.config['IMAGE_FOLDER'], cover_filename)

                # Resize image
                img = Image.open(cover_image)
                img.thumbnail((500, 500))
                img.save(cover_path)

        beat = Beat(
            title=title,
            description=description,
            price=price,
            bpm=bpm,
            genre=genre,
            audio_file=audio_filename,
            cover_image=cover_filename,
            user_id=current_user.id
        )

        db.session.add(beat)
        db.session.commit()
        flash('Beat uploaded successfully!')
        return redirect(url_for('profile'))

    return render_template('upload.html')


@app.route('/beat/<int:beat_id>')
def beat_detail(beat_id):
    beat = Beat.query.get_or_404(beat_id)
    is_purchased = False
    if current_user.is_authenticated:
        is_purchased = Purchase.query.filter_by(user_id=current_user.id, beat_id=beat_id).first() is not None
    return render_template('beat.html', beat=beat, is_purchased=is_purchased)


@app.route('/purchase/<int:beat_id>', methods=['POST'])
@login_required
def purchase_beat(beat_id):
    beat = Beat.query.get_or_404(beat_id)

    # Check if already purchased
    existing_purchase = Purchase.query.filter_by(user_id=current_user.id, beat_id=beat_id).first()
    if existing_purchase:
        flash('You already purchased this beat')
        return redirect(url_for('beat_detail', beat_id=beat_id))

    # In a real app, you would process payment here
    purchase = Purchase(user_id=current_user.id, beat_id=beat_id)
    db.session.add(purchase)
    db.session.commit()

    flash('Purchase successful!')
    return redirect(url_for('profile'))


@app.route('/marketplace')
def marketplace():
    page = request.args.get('page', 1, type=int)
    genre = request.args.get('genre', '')
    sort_by = request.args.get('sort', 'newest')

    query = Beat.query

    if genre:
        query = query.filter(Beat.genre == genre)

    if sort_by == 'price_low':
        query = query.order_by(Beat.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Beat.price.desc())
    else:  # newest
        query = query.order_by(Beat.created_at.desc())

    beats = query.paginate(page=page, per_page=12, error_out=False)

    genres = db.session.query(Beat.genre).distinct().all()
    genres = [g[0] for g in genres if g[0]]

    return render_template('marketplace.html', beats=beats, genres=genres, current_genre=genre, current_sort=sort_by)


@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        beats = Beat.query.filter(
            (Beat.title.contains(query)) |
            (Beat.description.contains(query)) |
            (Beat.genre.contains(query))
        ).all()
    else:
        beats = []

    return render_template('search.html', beats=beats, query=query)


@app.route('/audio/<filename>')
@login_required
def serve_audio(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
