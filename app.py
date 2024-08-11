from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from bson.objectid import ObjectId
from config import Config
from models import mongo, bcrypt, login_manager, User
from forms import RegistrationForm, LoginForm, IdeaForm, CommentForm, FilterForm, PostForm
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
csrf = CSRFProtect(app)

mongo.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = os.path.join(app.root_path, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': hashed_password
        }
        mongo.db.users.insert_one(user_data)
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    for error in form.errors.values():
        flash(f'{error[0]}', 'danger')
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = mongo.db.users.find_one({'email': form.email.data})
        if user and bcrypt.check_password_hash(user['password'], form.password.data):
            user_obj = User(user)
            login_user(user_obj, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    for error in form.errors.values():
        flash(f'{error[0]}', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    user_ideas = mongo.db.ideas.find({'author_id': ObjectId(current_user.id)})
    return render_template('profile.html', title='Profile', ideas=user_ideas)

@app.route('/submit-idea', methods=['GET', 'POST'])
@login_required
def submit_idea():
    form = IdeaForm()  # Using IdeaForm for submitting ideas
    if form.validate_on_submit():
        idea_data = {
            'title': form.title.data,
            'description': form.description.data,
            'domain': form.domain.data,
            'author_id': ObjectId(current_user.id),
            'author_name': current_user.username,
            'author_email': current_user.email,
            'upvotes': 0,
            'comments': []
        }
        mongo.db.ideas.insert_one(idea_data)
        flash('Idea submitted successfully!', 'success')
        return redirect(url_for('submit_idea'))
    return render_template('submit_idea.html', title='Submit Idea', form=form)

@app.route('/explore-ideas', methods=['GET', 'POST'])
@login_required
def explore_ideas():
    form = FilterForm()
    distinct_domains = mongo.db.ideas.distinct('domain')
    form.domain.choices = [(d, d) for d in distinct_domains]
    ideas = mongo.db.ideas.find()
    if form.validate_on_submit():
        domain = form.domain.data
        ideas = mongo.db.ideas.find({'domain': domain})
    return render_template('explore_ideas.html', title='Explore Ideas', ideas=ideas, form=form)

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    form = PostForm()
    posts = mongo.db.posts.find()
    if form.validate_on_submit():
        post_data = {
            'content': form.content.data,
            'author_id': ObjectId(current_user.id),
            'author_name': current_user.username
        }
        
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                post_data['file_url'] = url_for('static', filename='uploads/' + filename)
        
        mongo.db.posts.insert_one(post_data)
        flash('Post submitted successfully!', 'success')
        return redirect(url_for('post'))
    return render_template('post.html', title='Post Something', form=form, posts=posts)

@app.route('/idea/<idea_id>', methods=['GET', 'POST'])
@login_required
def idea_detail(idea_id):
    idea = mongo.db.ideas.find_one_or_404({'_id': ObjectId(idea_id)})
    form = CommentForm()
    if form.validate_on_submit():
        comment_data = {
            'author_id': ObjectId(current_user.id),
            'author_name': current_user.username,
            'text': form.comment_text.data
        }
        mongo.db.ideas.update_one({'_id': ObjectId(idea_id)}, {'$push': {'comments': comment_data}})
        flash('Your comment has been added!', 'success')
        return redirect(url_for('idea_detail', idea_id=idea_id))
    return render_template('idea_detail.html', title=idea['title'], idea=idea, form=form)

@app.route('/comment/<idea_id>', methods=['POST'])
@login_required
def comment(idea_id):
    idea = mongo.db.ideas.find_one({'_id': ObjectId(idea_id)})
    if idea:
        comment_text = request.form.get('comment_text')
        comment_data = {
            'author_id': ObjectId(current_user.id),
            'author_name': current_user.username,
            'text': comment_text
        }
        mongo.db.ideas.update_one({'_id': ObjectId(idea_id)}, {'$push': {'comments': comment_data}})
        flash('Your comment has been added!', 'success')
    else:
        flash('Idea not found.', 'danger')
    return redirect(url_for('idea_detail', idea_id=idea_id))

@app.route('/upvote/<idea_id>')
@login_required
def upvote(idea_id):
    mongo.db.ideas.update_one({'_id': ObjectId(idea_id)}, {'$inc': {'upvotes': 1}})
    return redirect(url_for('idea_detail', idea_id=idea_id))

if __name__ == '__main__':
    app.run(debug=True)
