from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired


class BooksForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField("Описание")
    genre = SelectField(label="Жанр", choices=("Хоррор", "Боевик", "Комедия"))
    file = FileField("Выбрать книгу")
    submit = SubmitField('Добавить')
