import os
from flask import Flask, flash, request, redirect, render_template, url_for, abort, session
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import config
import functions
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config.update(SECRET_KEY = config.SECRET_KEY)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id
    
    def __repr__(self):
        return self.id

user = User(0)

@app.route('/')
def home():
    if request.args.get('search'):
        articles = functions.get_articles_with_search(request.args.get('search'))
    elif request.args.get('category_id'):
        articles = functions.get_articles_with_category_id(request.args.get('category_id'))
    else:
        articles = functions.get_all_articles()
    return render_template('home.html', site_title = config.SITE_TITLE, categories = functions.get_all_categories(), articles = articles, user_authenticate = current_user.is_authenticated)

@app.route('/single-page/<int:id>')
def single_page(id):
    if not functions.get_article_with_id(id):
        abort(404)
    article = functions.get_article_with_id(id)
    if current_user.is_authenticated:
        show_commenter_name_input = False
    else:
        show_commenter_name_input = True
    if request.args.get('answer_to'):
        answer_to_comment = request.args.get('answer_to')
    else:
        answer_to_comment = False
    return render_template('single.html', article = article, article_category = functions.get_category_with_id(article[4]), site_title = config.SITE_TITLE, user_authenticate = current_user.is_authenticated, show_commenter_name_input = show_commenter_name_input, comments = functions.get_article_comments(id), answer_to_comment = answer_to_comment)

@app.route('/add-comment/<int:article_id>', methods = ['POST'])
def add_comment(article_id):
    if current_user.is_authenticated:
        user_name = 'مدیر سایت'
    else:
        user_name = request.form['name']
    if request.form['answer_to']:
        answer_to = "'" + str(request.form['answer_to']) + "'"
    else:
        answer_to = "NULL"
    functions.insert_comment({
        'user_name' : user_name,
        'comment' : request.form['comment'],
        'article_id' : article_id,
        'answer_to' : answer_to,
        'date' : functions.get_current_time()
    })
    return redirect(f'/single-page/{article_id}#end_comments')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if not request.form['username']:
            flash('لطفا نام کاربری خود را وارد کنید.', 'danger')
            return redirect(url_for('login'))
        if not request.form['password']:
            session[config.FIRST_OF_SESSIONS + '_login_username'] = request.form['username']
            flash('لطفا رمز عبور خود را وارد کنید.', 'danger')
            return redirect(url_for('login'))
        if request.form['username'] != config.ADMIN_USERNAME:
            flash('نام کاربری صحیح نمی باشد. لطفا مجددا تلاش کنید.', 'danger')
            return redirect(url_for('login'))
        if request.form['password'] != config.ADMIN_PASSWORD:
            session[config.FIRST_OF_SESSIONS + '_login_username'] = request.form['username']
            flash('رمز عبور صحیح نمی باشد. لطفا مجددا تلاش کنید.', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        flash('شما با موفقیت وارد شدید.', 'success')
        return redirect(url_for('dashboard'))
    if session.get(config.FIRST_OF_SESSIONS + '_login_username') == None:
        username_value = ''
    else:
        username_value = session[config.FIRST_OF_SESSIONS + '_login_username']
        del session[config.FIRST_OF_SESSIONS + '_login_username']
    return render_template('login.html', username_value = username_value, site_title = config.SITE_TITLE)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('شما با موفقیت از حساب کاربری خود خارج شدید!', 'success')
    return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    if request.args.get('edit-category'):
        show_form = 'edit_category'
        name_input_value = functions.get_category_with_id(request.args.get('edit-category'))[1]
    else:
        show_form = 'add_category'
        name_input_value = ''
    return render_template('dashboard.html', site_title = config.SITE_TITLE, show_form = show_form, categories = functions.get_all_categories(), all_articles = functions.get_all_articles_with_counter(), name_input_value = name_input_value)

@app.route('/insert-category', methods = ['POST'])
@login_required
def insert_category():
    name = request.form['name']
    if functions.check_category_exists('name', name):
        flash('نام دسته بندی شما وجود دارد و نمی توانید مجددا دسته بندی با همین نام ایجاد کنید.', 'danger')
        return redirect(url_for('dashboard'))
    functions.insert_category(name)
    flash(f'دسته بندی «{name}» با موفقیت اضافه شد.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/update-category/<int:id>', methods = ['POST'])
@login_required
def update_category(id):
    old_name = functions.get_category_with_id(id)[1]
    name = request.form['name']
    if name != old_name and functions.check_category_exists('name', name):
        flash('نام دسته بندی شما وجود دارد و نمی توانید مجددا دسته بندی با همین نام ایجاد کنید.', 'danger')
        return redirect(url_for('dashboard'))
    if not functions.check_category_exists('id', id):
        flash('دسته بندی مورد نظر شما یافت نشد!', 'warning')
        return redirect(url_for('dashboard'))
    functions.update_category(id, name)
    flash(f"دسته بندی «{old_name}» با موفقیت به «{name}» تغییر نام داده شد.", 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete-category/<int:id>')
@login_required
def delete_category(id): #TODO: delete articles for this category
    if not functions.check_category_exists('id', id):
        flash('دسته بندی مورد نظر شما یافت نشد!', 'warning')
        return redirect(url_for('dashboard'))
    category_name = functions.get_category_with_id(id)[1]
    functions.delete_category(id)
    #TODO: change category for articles that are for this category.
    flash(f'دسته بندی «{category_name}» با موفقیت حذف شد.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add-article')
@login_required
def add_article():
    return render_template('add_article.html', site_title = config.SITE_TITLE, categories = functions.get_all_categories())

@app.route('/insert-article', methods = ['POST'])
@login_required
def insert_article():
    if 'image' not in request.files:
        flash('فایل مورد نظر شما یافت نشد!', 'danger')
        return redirect(url_for('add_article'))
    image = request.files['image']
    if not image or not image.filename:
        flash('فایل انتخاب شده توسط شما مقدار درستی ندارد.', 'danger')
        return redirect(url_for('add_article'))
    if not functions.allow_to_files(image.filename):
        flash('پسوند فایل شما قابل قبول نیست. لطفا تصویری با فرمت دیگر آپلود کنید.', 'danger')
        return redirect(url_for('add_article'))
    information = {}
    information['image_filename'] = secure_filename(image.filename)
    information['name'] = request.form['name']
    information['description'] = request.form['description']
    information['category'] = request.form['category']
    information['full_time'] = functions.get_current_time()
    inserted_article_id = functions.insert_article(information)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], inserted_article_id + '_' + information['image_filename']))
    functions.update_article_image_name(inserted_article_id, inserted_article_id + '_' + information['image_filename'])
    flash(f"مقاله «{information['name']}» توسط شما با موفقیت اضافه شد.", 'success')
    return redirect(url_for('dashboard'))

@app.route('/edit-article/<int:id>')
@login_required
def edit_article(id):
    article = functions.get_article_with_id(id, 1)
    categories = functions.get_all_categories()
    return render_template('edit_article.html', site_title = config.SITE_TITLE, categories = categories, article = article)

@app.route('/update-article/<int:id>', methods = ['POST'])
@login_required
def update_article(id):
    old_article = functions.get_article_with_id(id, 1)
    if request.files['image'] and request.files['image'].filename:
        image = request.files['image']
        if not functions.allow_to_files(image.filename):
            flash('پسوند فایل شما قابل قبول نمی باشد. لطفا مجددا تلاش کنید.', 'danger')
            return redirect(f'/edit-article/{id}')
        else:
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], str(id) + '_' + secure_filename(image.filename)))
            os.remove(app.config['UPLOAD_FOLDER'] + old_article[2])
            functions.update_article_image_name(id, str(id) + '_' + secure_filename(image.filename))
    functions.update_article(id, {
        'name': request.form['name'],
        'description': request.form['description'],
        'category': request.form['category']
    })
    flash("مقاله مورد نظر شما با موفقیت ویرایش شد.", 'success')
    return redirect(url_for('dashboard'))

@app.route('/send-article-to-trash/<int:id>')
@login_required
def send_article_to_trash(id):
    article_name = functions.get_article_with_id(id)[1]
    functions.transfer_article_to_trash(id)
    flash(f"مقاله «{article_name}» با موفقیت به سطل زباله انتقال داده شد.", 'success')
    return redirect(url_for('dashboard'))

@app.route('/trash')
@login_required
def trash():
    return render_template('trash.html', site_title = config.SITE_TITLE, all_articles = functions.get_all_articles_with_counter(0, 'delete_date'))

@app.route('/delete-article/<int:id>')
@login_required
def delete_article(id):
    article_name = functions.get_article_with_id(id, 0)[1]
    functions.delete_article(id)
    flash(f"مقاله «{article_name}» با موفقیت حذف شد.", 'success')
    return redirect(url_for('trash'))

@app.route('/restore-article-from-trash/<int:id>')
@login_required
def restore_article_from_trash(id):
    article_name = functions.get_article_with_id(id, 0)[1]
    functions.restore_article_from_trash(id)
    flash(f"مقاله «{article_name}» با موفقیت از سطل زباله بازیابی شد.", 'success')
    return redirect(url_for('dashboard'))

@login_manager.user_loader
def user_load(id):
    return user

@app.errorhandler(404)
def page_not_found(e):
    return 'page not found.' #TODO: return a html file for it and add other HTTP errors.

if __name__ == '__main__':
    app.run(debug=True)
