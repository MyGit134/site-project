from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired


class BanForm(FlaskForm):
    reason = TextAreaField("Причина блокировки:", validators=[DataRequired()])
    submit = SubmitField('Заблокировать')
