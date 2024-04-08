from flask import Flask, render_template, redirect, request, send_file, abort
from io import BytesIO
from forms.loginform import LoginForm
from forms.books import BooksForm
from data import db_session
from data.users import User
from data.books import Books
from forms.reg import RegisterForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data.upload import Upload
import datetime

app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)
app.config['SECRET_KEY'] = 'leon_0152759'
app.config['UPLOAD_FOLDER'] = "/all_books"
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    mod = False
    if current_user.is_authenticated:
        if current_user.moderator:
            mod = True
            books = db_sess.query(Books)
        else:
            books = db_sess.query(Books).filter((Books.user == current_user) | (Books.under_moderation != True))
    else:
        books = db_sess.query(Books).filter(Books.under_moderation != True)
    return render_template("index.html", books=books, mod=mod)


@app.route('/book/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    form = BooksForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        books = db_sess.query(Books).filter(Books.id == id,
                                            (Books.user == current_user or current_user.moderator)).first()
        if books:
            form.name.data = books.name
            form.genre.data = books.main_genre
            form.description.data = books.description
            form.genre.data = books.main_genre
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        books = db_sess.query(Books).filter(Books.id == id,
                                            (Books.user == current_user or current_user.moderator)).first()
        if books or current_user.moderator:
            bookfile = request.files["bookfile"]
            fl = db_sess.query(Upload).filter(id == id).first()
            fl.creator_email = current_user.email
            fl.file = bookfile.read()
            fl.book_name = form.name.data
            books.name = form.name.data
            books.description = form.description.data
            books.main_genre = form.genre.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('books.html', title='Редактирование книги', form=form)


@app.route('/books', methods=['GET', 'POST'])
@login_required
def add_book():
    form = BooksForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        books = Books()
        books.name = form.name.data
        books.description = form.description.data
        books.main_genre = form.genre.data
        bookfile = request.files["bookfile"]
        upload = Upload(book_name=books.name, creator_email=current_user.email, file=bookfile.read())
        db_sess.add(upload)
        current_user.books.append(books)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('books.html', title='Добавление книги',
                           form=form)


@app.route('/public/<int:id>', methods=['GET', 'POST'])
@login_required
def public(id):
    db_sess = db_session.create_session()
    book = db_sess.query(Books).filter(Books.id == id).first()
    if book:
        book.under_moderation = False
        db_sess.commit()
    return redirect("/")


@app.route("/description/<int:id>", methods=["GET"])
def desc(id):
    db_sess = db_session.create_session()
    book = db_sess.query(Books).filter(Books.id == id).first()
    if book:
        return render_template("desc.html", book=book)
    else:
        abort(404)


@app.route("/download/<int:id>")
def download(id):
    db_sess = db_session.create_session()
    download = db_sess.query(Upload).filter(Upload.id == id).first()
    return send_file(BytesIO(download.file), download_name=f"{download.book_name}.txt", as_attachment=True)


@app.route('/book_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def books_delete(id):
    db_sess = db_session.create_session()
    books = db_sess.query(Books).filter(Books.id == id, (Books.user == current_user or current_user.moderator)).first()
    file = db_sess.query(Upload).filter(Books.id == id, (Books.user == current_user or current_user.moderator)).first()
    if books and file:
        db_sess.delete(books)
        db_sess.delete(file)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


def main():
    db_session.global_init("db/books.db")
    app.run()


if __name__ == '__main__':
    main()
