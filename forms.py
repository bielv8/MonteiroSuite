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
    whatsapp = StringField('WhatsApp', validators=[Optional(), Length(max=20)])
    cpf_cnpj = StringField('CPF/CNPJ', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Endereço', validators=[Optional()])
    city = StringField('Cidade', validators=[Optional(), Length(max=100)])
    state = SelectField('Estado', choices=[
        ('', 'Selecione...'),
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ], validators=[Optional()])
    zip_code = StringField('CEP', validators=[Optional(), Length(max=10)])
    birth_date = DateField('Data de Nascimento', validators=[Optional()])
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
    responsible_id = SelectField('Responsável', coerce=int, validators=[Optional()])
    priority = SelectField('Prioridade', choices=[
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta')
    ], default='normal')
    due_date = DateField('Data de Vencimento', validators=[Optional()])

class UserForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    name = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('Senha', validators=[Optional(), Length(min=6)])
    role = SelectField('Função', choices=[
        ('user', 'Usuário'),
        ('manager', 'Gerente'),
        ('admin', 'Administrador')
    ], default='user')
    active = BooleanField('Ativo', default=True)

class WhatsAppMessageForm(FlaskForm):
    phone_number = StringField('Número do WhatsApp', validators=[DataRequired(), Length(max=20)])
    message = TextAreaField('Mensagem', validators=[DataRequired()], widget=TextArea())
