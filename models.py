from datetime import datetime
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, manager, user
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    kanban_cards = db.relationship('KanbanCard', backref='responsible_user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role in ['admin', 'manager']

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    cpf_cnpj = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    birth_date = db.Column(db.Date)
    insurance_type = db.Column(db.String(50))  # auto, vida, residencial, empresarial
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='ativo')  # ativo, inativo, prospect
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    policies = db.relationship('Policy', backref='client', lazy=True)
    kanban_cards = db.relationship('KanbanCard', backref='client', lazy=True)
    whatsapp_messages = db.relationship('WhatsAppMessage', backref='client', lazy=True)
    
    def __repr__(self):
        return f'<Client {self.name}>'

class Policy(db.Model):
    __tablename__ = 'policies'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    policy_number = db.Column(db.String(50), unique=True, nullable=False)
    insurance_company = db.Column(db.String(100), nullable=False)
    insurance_type = db.Column(db.String(50), nullable=False)
    coverage_amount = db.Column(db.Numeric(12, 2))
    premium_amount = db.Column(db.Numeric(10, 2), nullable=False)
    commission_rate = db.Column(db.Numeric(5, 2))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='ativa')  # ativa, vencida, cancelada
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Policy {self.policy_number}>'

class KanbanColumn(db.Model):
    __tablename__ = 'kanban_columns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), default='#007bff')  # Hex color
    order_position = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    cards = db.relationship('KanbanCard', backref='column', lazy=True, order_by='KanbanCard.order_position')
    
    def __repr__(self):
        return f'<KanbanColumn {self.name}>'

class KanbanCard(db.Model):
    __tablename__ = 'kanban_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    column_id = db.Column(db.Integer, db.ForeignKey('kanban_columns.id'), nullable=False)
    responsible_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    priority = db.Column(db.String(10), default='normal')  # alta, normal, baixa
    due_date = db.Column(db.Date)
    order_position = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<KanbanCard {self.title}>'

class WhatsAppMessage(db.Model):
    __tablename__ = 'whatsapp_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    phone_number = db.Column(db.String(20), nullable=False)
    message_id = db.Column(db.String(100))  # WhatsApp message ID
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, image, document
    direction = db.Column(db.String(10), nullable=False)  # incoming, outgoing
    status = db.Column(db.String(20), default='sent')  # sent, delivered, read, failed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WhatsAppMessage {self.phone_number}>'

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activity_logs')
    
    def __repr__(self):
        return f'<ActivityLog {self.action}>'
