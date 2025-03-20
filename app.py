from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8c41f2fb9978613a77bb6c02d6c67938'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -------------------------
# Models
# -------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(150), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------------
# User Loader
# -------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------
# Database Initialization & Sample Data
# -------------------------
@app.before_first_request
def create_tables():
    db.drop_all()  # For development only. Remove in production.
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('admin')  # default: admin/admin
        db.session.add(admin)
    if Event.query.count() == 0:
        sample_events = [
            Event(
                title="Sample Event 1",
                description="This is a sample event to show you how events look.",
                event_date=datetime(2025, 3, 20).date(),
                event_time=datetime(2025, 3, 20, 15, 0).time(),
                location="Conference Room A"
            ),
            Event(
                title="Sample Event 2",
                description="Another sample event with a different description.",
                event_date=datetime(2025, 3, 25).date(),
                event_time=datetime(2025, 3, 25, 10, 30).time(),
                location="Main Hall"
            ),
            Event(
                title="Sample Event 3",
                description="This sample event helps you see a complete event list.",
                event_date=datetime(2025, 4, 5).date(),
                event_time=datetime(2025, 4, 5, 18, 0).time(),
                location="Auditorium"
            ),
        ]
        for ev in sample_events:
            db.session.add(ev)
    db.session.commit()

# -------------------------
# Context Processor
# -------------------------
@app.context_processor
def inject_events():
    if current_user.is_authenticated:
        events = Event.query.order_by(Event.event_date, Event.event_time).all()
    else:
        events = []
    return dict(events=events)

# -------------------------
# Authentication Routes
# -------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm = request.form['confirm']
        if password != confirm:
            flash("Passwords do not match.")
            return redirect(url_for('signup'))
        if User.query.filter((User.username==username)|(User.email==email)).first():
            flash("Username or Email already exists.")
            return redirect(url_for('signup'))
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup successful! Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully!")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!")
    return redirect(url_for('login'))

# -------------------------
# Event Management (CRUD)
# -------------------------
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date = request.form['event_date']
        event_time = request.form['event_time']
        location = request.form['location']
        try:
            event_date_obj = datetime.strptime(event_date, '%Y-%m-%d').date()
            event_time_obj = datetime.strptime(event_time, '%H:%M').time()
        except ValueError:
            flash("Invalid date or time format.")
            return redirect(url_for('add_event'))
        new_event = Event(title=title, description=description,
                          event_date=event_date_obj, event_time=event_time_obj, location=location)
        db.session.add(new_event)
        db.session.commit()
        flash("Event added successfully!")
        return redirect(url_for('index'))
    return render_template('add_event.html')

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        event.title = request.form['title']
        event.description = request.form['description']
        event_date = request.form['event_date']
        event_time = request.form['event_time']
        event.location = request.form['location']
        try:
            event.event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
            event.event_time = datetime.strptime(event_time, '%H:%M').time()
        except ValueError:
            flash("Invalid date or time format.")
            return redirect(url_for('edit_event', event_id=event_id))
        db.session.commit()
        flash("Event updated successfully!")
        return redirect(url_for('index'))
    return render_template('edit_event.html', event=event)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully!")
    return redirect(url_for('index'))

@app.route('/search')
@login_required
def search():
    query = request.args.get('query', '')
    if query:
        events = Event.query.filter(
            (Event.title.ilike(f'%{query}%')) |
            (Event.description.ilike(f'%{query}%')) |
            (Event.location.ilike(f'%{query}%'))
        ).all()
    else:
        events = []
    return render_template('search_results.html', events=events, query=query)

# -------------------------
# Additional Features
# -------------------------
@app.route('/event/<int:event_id>')
@login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    event_datetime = datetime.combine(event.event_date, event.event_time)
    return render_template('event_detail.html', event=event, event_datetime=event_datetime)

@app.route('/download_ics/<int:event_id>')
@login_required
def download_ics(event_id):
    event = Event.query.get_or_404(event_id)
    event_datetime = datetime.combine(event.event_date, event.event_time)
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dtstart = event_datetime.strftime("%Y%m%dT%H%M%SZ")
    dtend = (event_datetime + timedelta(hours=1)).strftime("%Y%m%dT%H%M%SZ")
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Your Company//Event Manager//EN
BEGIN:VEVENT
UID:{event.id}@yourcompany.com
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{event.title}
DESCRIPTION:{event.description}
LOCATION:{event.location}
END:VEVENT
END:VCALENDAR
"""
    return Response(ics_content, mimetype='text/calendar', headers={"Content-Disposition": f"attachment; filename=event_{event.id}.ics"})

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        contact_msg = ContactMessage(name=name, email=email, message=message)
        db.session.add(contact_msg)
        db.session.commit()
        flash("Thank you for your message. We'll get back to you soon!")
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/set_reminder/<int:event_id>', methods=['POST'])
@login_required
def set_reminder(event_id):
    email = request.form['email']
    reminder = Reminder(email=email, event_id=event_id)
    db.session.add(reminder)
    db.session.commit()
    flash("Reminder set successfully! You'll be notified before the event.")
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/gallery')
def gallery():
    gallery_images = os.listdir(os.path.join(app.root_path, 'static', 'images', 'gallery'))
    return render_template('gallery.html', images=gallery_images)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        email = request.form['email']
        message = request.form['message']
        feedback_entry = Feedback(email=email, message=message)
        db.session.add(feedback_entry)
        db.session.commit()
        flash("Thank you for your feedback!")
        return redirect(url_for('feedback'))
    return render_template('feedback.html')

@app.route('/dashboard')
@login_required
def dashboard():
    events_count = Event.query.count()
    contacts_count = ContactMessage.query.count()
    feedback_count = Feedback.query.count()
    reminders_count = Reminder.query.count()
    return render_template('dashboard.html', events_count=events_count,
                           contacts_count=contacts_count, feedback_count=feedback_count,
                           reminders_count=reminders_count)

if __name__ == '__main__':
    app.run(debug=True)
