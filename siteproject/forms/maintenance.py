from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired


class Maintenance(FlaskForm):
    reason = TextAreaField("Закрытие сайта:", validators=[DataRequired()])
    submit = SubmitField('Активировать')
    cancel = SubmitField('Отменить')
