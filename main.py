from imports import *  # Импорт всех библиотек из файла "imports.py"

app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)
app.config['SECRET_KEY'] = 'leon_0152759'
getLogger('werkzeug').setLevel(ERROR)
login_manager = LoginManager()
login_manager.init_app(app)


@app.route("/disable-css")
def disable_css():
    if "disable_css" not in session:
        session["disable_css"] = True
    else:
        session.pop("disable_css", None)
    return redirect('/')


def moderator_action(action, user, book=None):
    db_sess = db_session.create_session()
    log = History()
    log.moderator = current_user.email
    log.action = action
    log.user = user
    log.book = book
    db_sess.add(log)
    db_sess.commit()


@app.route('/owner/cancel')
def cancel():
    if current_user.email == 'leon134134@yandex.ru':
        global maintenance
        maintenance = False
        return redirect('/owner')
    else:
        return abort(404)


@app.route('/history', methods=['POST', 'GET'])
def history():
    db_sess = db_session.create_session()
    email = request.form['modemail']
    results = db_sess.query(History).filter(History.moderator == email).order_by(History.id.desc()).all()
    if results:
        return render_template('history.html', data=results)
    else:
        flash("Ошибка: Модератора не существует или модератор ещё не совершал никаких действий.", 'error')
        return redirect('/owner')


@app.route("/owner", methods=['POST', 'GET'])
@login_required
def owner():
    if current_user.email != "leon134134@yandex.ru":
        return abort(404)
    if request.method == "POST":
        if request.form["close"] == "close":
            global maintenance
            maintenance = True
            global reason
            reason = request.form['reason']
        else:
            print(request.form['actions'])
    if current_user.email == "leon134134@yandex.ru":
        messages = get_flashed_messages(with_categories=True)
        return render_template('ownermenu.html', form=Maintenance(), messages=messages)
    else:
        abort(404)


@app.route("/complete", methods=['POST'])
@login_required
def complete():
    if current_user.email != "leon134134@yandex.ru":
        return abort(404)
    query = request.form["actions"]
    emailinput = request.form["emailinput"]
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == emailinput).first()
    if not user:
        flash("Ошибка: пользователя с таким адресом электронной почты не существует.", 'error')
        return redirect('/owner')
    if query == 'modban':
        user.banned = True
    elif query == 'unban':
        user.banned = False
        user.ban_reason = None
    elif query == 'givemod':
        user.moderator = True
    elif query == 'takemod':
        user.moderator = False
    elif query == 'verify':
        user.verified = True
    elif query == 'unverify':
        user.verified = False
    db_sess.commit()
    db_sess.expunge_all()
    db_sess.close()
    return redirect('/owner')


@app.route("/sort", methods=['POST'])
def sort():
    query = request.form["genres"]
    db_sess = db_session.create_session()
    try:
        if current_user.moderator == False:
            results = db_sess.query(Books).filter((Books.main_genre == query) & (Books.under_moderation != True) | (
                    (Books.main_genre == query) & (Books.user == current_user)))
        else:
            results = db_sess.query(Books).filter(Books.main_genre == query)
    except AttributeError:
        results = db_sess.query(Books).filter((Books.main_genre == query) & (Books.under_moderation != True))
    db_sess.expunge_all()
    db_sess.close()
    return render_template("index.html", books=results)


@app.route("/find", methods=['POST'])
def find():
    query = request.form['query']
    db_sess = db_session.create_session()
    try:
        if current_user.moderator == False:
            results = db_sess.query(Books).filter(
                (Books.name.contains(query) == True) & (Books.under_moderation != True) | (
                        (Books.name.contains(query) == True) & (Books.user == current_user)))
        else:
            results = db_sess.query(Books).filter(Books.name.contains(query) == True)
    except AttributeError:
        results = db_sess.query(Books).filter((Books.name.contains(query) == True) & (Books.under_moderation != True))
    db_sess.expunge_all()
    db_sess.close()
    return render_template('index.html', books=results)


@app.route("/ban/<int:id>", methods=['GET', 'POST'])
@login_required
def ban(id):
    if maintenance:
        return render_template('maintenance.html', reason=reason)
    form = BanForm()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if form.validate_on_submit() and current_user.moderator == True and user.moderator == False:
        user.banned = True
        user.ban_reason = form.reason.data
        db_sess.commit()
        moderator_action('ban', user=user.email)
        return redirect("/")
    if user and current_user.moderator == True and user.moderator == False:
        db_sess.expunge_all()
        db_sess.close()
        return render_template("ban.html", user=user.name, form=form)
    else:
        return abort(404)


@app.route("/unban/<int:id>", methods=['GET'])
def unban(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if user.banned == True and current_user.moderator == True and user.moderator == False:
        user.banned = False
        user.ban_reason = None
        db_sess.commit()
        db_sess.expunge_all()
        db_sess.close()
        return redirect("/")
    return abort(404)


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
    if maintenance:
        return render_template('maintenance.html', reason=reason)
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
    if maintenance:
        return render_template('maintenance.html', reason=reason)
    db_sess = db_session.create_session()
    mod = False
    try:
        check = db_sess.query(User).filter(User.id == current_user.id).first()
        if check.banned == True:
            db_sess.expunge_all()
            db_sess.close()
            return render_template("ban_page.html", reason=check.ban_reason)
    except AttributeError:
        pass
    if current_user.is_authenticated:
        if current_user.moderator:
            mod = True
            books = db_sess.query(Books).order_by(Books.id.desc())
        else:
            books = db_sess.query(Books).order_by(Books.id.desc()).filter(
                (Books.user == current_user) | (Books.under_moderation != True))
    else:
        books = db_sess.query(Books).filter(Books.under_moderation != True).order_by(Books.id.desc())
    db_sess.expunge_all()
    db_sess.close()
    return render_template("index.html", books=books, mod=mod)


@app.route("/view/<int:id>")
def view(id):
    if maintenance:
        return render_template('maintenance.html', reason=reason)
    db_sess = db_session.create_session()
    try:
        check = db_sess.query(User).filter(User.id == current_user.id).first()
        if check.banned == True:
            db_sess.expunge_all()
            db_sess.close()
            return render_template("ban_page.html", reason=check.ban_reason)
    except AttributeError:
        pass
    book = db_sess.query(Upload).filter(Upload.id == id).first()
    lines = len(BytesIO(book.file).readlines())
    file = BytesIO(book.file)
    if lines > 100:
        lines = 100
    db_sess.expunge_all()
    db_sess.close()
    return render_template("view.html", file=file, book=book, lines=lines)


@app.route('/book/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    if maintenance:
        return render_template('maintenance.html', reason=reason)
    db_sess = db_session.create_session()
    try:
        check = db_sess.query(User).filter(User.id == current_user.id).first()
        if check.banned == True:
            db_sess.expunge_all()
            db_sess.close()
            return render_template("ban_page.html", reason=check.ban_reason)
    except AttributeError:
        pass
    form = BooksForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        books = db_sess.query(Books).filter(Books.id == id and
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
        books = db_sess.query(Books).filter(Books.id == id and
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
            db_sess.expunge_all()
            db_sess.close()
            return redirect('/')
        else:
            abort(404)
    return render_template('books.html', title='Редактирование книги', form=form)


@app.route('/books', methods=['GET', 'POST'])
@login_required
def add_book():
    if maintenance:
        return render_template('maintenance.html', reason=reason)
    form = BooksForm()
    db_sess = db_session.create_session()
    try:
        check = db_sess.query(User).filter(User.id == current_user.id).first()
        if check.banned == True:
            return render_template("ban_page.html", reason=check.ban_reason)
    except AttributeError:
        pass
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        books = Books()
        books.name = form.name.data
        books.description = form.description.data
        books.main_genre = form.genre.data
        if current_user.verified == True:
            books.under_moderation = False
        bookfile = request.files["bookfile"]
        upload = Upload(book_name=books.name, creator_email=current_user.email, file=bookfile.read())
        db_sess.add(upload)
        current_user.books.append(books)
        db_sess.merge(current_user)
        db_sess.commit()
        db_sess.expunge_all()
        db_sess.close()
        return redirect('/')
    return render_template('books.html', title='Добавление книги',
                           form=form)


@app.route('/public/<int:id>', methods=['GET', 'POST'])
@login_required
def public(id):
    if maintenance:
        return render_template('maintenance.html', reason=reason)
    db_sess = db_session.create_session()
    try:
        check = db_sess.query(User).filter(User.id == current_user.id).first()
        if check.banned == True:
            return render_template("ban_page.html", reason=check.ban_reason)
    except AttributeError:
        pass
    book = db_sess.query(Books).filter(Books.id == id).first()
    if book and current_user.moderator:
        book.under_moderation = False
        db_sess.commit()
        moderator_action("public", book=book.name, user=book.user.email)
    return redirect("/")


@app.route("/description/<int:id>", methods=["GET"])
def desc(id):
    if maintenance:
        return render_template('maintenance.html', reason=reason)
    db_sess = db_session.create_session()
    try:
        check = db_sess.query(User).filter(User.id == current_user.id).first()
        if check.banned == True:
            db_sess.expunge_all()
            db_sess.close()
            return render_template("ban_page.html", reason=check.ban_reason)
    except AttributeError:
        pass
    book = db_sess.query(Books).filter(Books.id == id).first()
    if book:
        db_sess.expunge_all()
        db_sess.close()
        return render_template("desc.html", book=book)
    else:
        abort(404)


@app.route("/download/<int:id>")
def download(id):
    if maintenance:
        return render_template('maintenance.html', reason=reason)
    db_sess = db_session.create_session()
    try:
        check = db_sess.query(User).filter(User.id == current_user.id).first()
        if check.banned == True:
            db_sess.expunge_all()
            db_sess.close()
            return render_template("ban_page.html", reason=check.ban_reason)
    except AttributeError:
        pass
    download = db_sess.query(Upload).filter(Upload.id == id).first()
    db_sess.expunge_all()
    db_sess.close()
    return send_file(BytesIO(download.file), download_name=f"{download.book_name}.txt", as_attachment=True)


@app.route('/book_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def books_delete(id):
    if maintenance:
        return render_template('maintenance.html', reason=reason)
    db_sess = db_session.create_session()
    try:
        check = db_sess.query(User).filter(User.id == current_user.id).first()
        if check.banned == True:
            db_sess.expunge_all()
            db_sess.close()
            return render_template("ban_page.html", reason=check.ban_reason)
    except AttributeError:
        pass
    books = db_sess.query(Books).filter(
        Books.id == id and (Books.user == current_user or current_user.moderator)).first()
    file = db_sess.query(Upload).filter(Upload.id == id and (Upload.creator_email == current_user.email or current_user.
                                                             moderator)).first()
    if books and file:
        db_sess.delete(books)
        db_sess.delete(file)
        db_sess.commit()
        if books.user != current_user and current_user.moderator:
            moderator_action('remove', book=books.name, user=books.user.email)
    else:
        abort(404)
    db_sess.expunge_all()
    db_sess.close()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    if maintenance:
        return render_template('maintenance.html', reason=reason)
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
        db_sess.expunge_all()
        db_sess.close()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


def main():
    db_session.global_init("db/books.db")
    app.run()


if __name__ == '__main__':
    maintenance = False
    main()
