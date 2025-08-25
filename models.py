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
    role = db.Column(db.String(20), default='user')  # admin, user
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_admin(self):
        return self.role == 'admin'

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    insurance_type = db.Column(db.String(50))  # auto, vida, residencial, empresarial
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='ativo')  # ativo, inativo, prospect
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Client {self.name}>'

# Removido Policy para simplificar

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
    priority = db.Column(db.String(10), default='normal')  # alta, normal, baixa
    order_position = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<KanbanCard {self.title}>'

# Removidas funcionalidades pesadas para otimização
