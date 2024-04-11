from flask import Flask, render_template, redirect, request, send_file, abort, flash, get_flashed_messages
from io import BytesIO
from forms.ban import BanForm
from forms.loginform import LoginForm
from forms.books import BooksForm
from forms.maintenance import Maintenance
from data import db_session
from data.users import User
from data.books import Books
from data.history import History
from forms.reg import RegisterForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data.upload import Upload
from logging import getLogger, ERROR
import datetime
