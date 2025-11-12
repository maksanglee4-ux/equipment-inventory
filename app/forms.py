from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, SelectField, FloatField
from wtforms.validators import DataRequired, Length, Optional

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('ФИО', validators=[DataRequired(), Length(min=1, max=64)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    is_admin = SelectField('Роль', choices=[('False', 'МОЛ'), ('True', 'Администратор')])
    submit = SubmitField('Зарегистрироваться')

class UserForm(FlaskForm):
    username = StringField('ФИО', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[Optional()])
    is_admin = SelectField('Роль', choices=[('False', 'МОЛ'), ('True', 'Администратор')])
    submit = SubmitField('Сохранить')

class ImportForm(FlaskForm):
    file = FileField('Файл (Excel)', validators=[DataRequired()])
    submit = SubmitField('Импорт')

class TransferForm(FlaskForm):
    new_mol = StringField('Новый МОЛ (логин)', validators=[DataRequired()])
    submit = SubmitField('Передать')

class LocationForm(FlaskForm):
    new_location = StringField('Новое местоположение', validators=[DataRequired()])
    submit = SubmitField('Переместить')

class EquipmentForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    barcode = StringField('Штрих-код', validators=[DataRequired()])
    location = StringField('Местоположение', validators=[DataRequired()])
    status = SelectField('Статус', choices=[('на балансе', 'На балансе'), ('списано', 'Списано')])
    inventory_number = StringField('Инвентарный номер')
    cost = FloatField('Стоимость')
    submit = SubmitField('Сохранить')