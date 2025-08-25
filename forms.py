from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, DecimalField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')

class ClientForm(FlaskForm):
    name = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    insurance_type = SelectField('Tipo de Seguro', choices=[
        ('', 'Selecione...'),
        ('auto', 'Auto'),
        ('vida', 'Vida'),
        ('residencial', 'Residencial'),
        ('empresarial', 'Empresarial'),
        ('saude', 'Saúde'),
        ('viagem', 'Viagem')
    ], validators=[Optional()])
    notes = TextAreaField('Observações', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('prospect', 'Prospect'),
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo')
    ], default='prospect')

class KanbanCardForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Descrição', validators=[Optional()])
    client_id = SelectField('Cliente', coerce=int, validators=[Optional()])
    priority = SelectField('Prioridade', choices=[
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta')
    ], default='normal')

class UserForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    name = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('Senha', validators=[Optional(), Length(min=6)])
    role = SelectField('Função', choices=[
        ('user', 'Usuário'),
        ('admin', 'Administrador')
    ], default='user')
    active = BooleanField('Ativo', default=True)

# WhatsApp form removido para otimização
