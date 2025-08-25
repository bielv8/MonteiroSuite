from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
import logging

from app import app, db
from models import User, Client, Policy, KanbanColumn, KanbanCard, WhatsAppMessage, ActivityLog
from forms import LoginForm, ClientForm, KanbanCardForm, UserForm, WhatsAppMessageForm
from whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)

def log_activity(action, description=None):
    """Log user activity"""
    if current_user.is_authenticated:
        log = ActivityLog(
            user_id=current_user.id,
            action=action,
            description=description,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.active:
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                log_activity('login', 'Usuário fez login no sistema')
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Sua conta está inativa. Entre em contato com o administrador.', 'warning')
        else:
            flash('Usuário ou senha incorretos.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    log_activity('logout', 'Usuário fez logout do sistema')
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get dashboard statistics
    total_clients = Client.query.count()
    active_clients = Client.query.filter_by(status='ativo').count()
    prospects = Client.query.filter_by(status='prospect').count()
    
    # Get recent activities
    recent_activities = ActivityLog.query.order_by(
        ActivityLog.timestamp.desc()
    ).limit(10).all()
    
    # Get kanban statistics
    kanban_stats = {}
    columns = KanbanColumn.query.filter_by(active=True).order_by(KanbanColumn.order_position).all()
    for column in columns:
        kanban_stats[column.name] = KanbanCard.query.filter_by(column_id=column.id).count()
    
    # Get recent WhatsApp messages
    recent_messages = WhatsAppMessage.query.order_by(
        WhatsAppMessage.timestamp.desc()
    ).limit(5).all()
    
    # Get policies expiring soon (next 30 days)
    from datetime import timedelta
    thirty_days_from_now = date.today() + timedelta(days=30)
    expiring_policies = Policy.query.filter(
        Policy.end_date <= thirty_days_from_now,
        Policy.status == 'ativa'
    ).count()
    
    return render_template('dashboard.html',
                         total_clients=total_clients,
                         active_clients=active_clients,
                         prospects=prospects,
                         recent_activities=recent_activities,
                         kanban_stats=kanban_stats,
                         recent_messages=recent_messages,
                         expiring_policies=expiring_policies)

@app.route('/kanban')
@login_required
def kanban():
    # Initialize default columns if they don't exist
    if KanbanColumn.query.count() == 0:
        default_columns = [
            ('Atendimento Inicial', '#17a2b8', 1),
            ('Propostas Enviadas', '#ffc107', 2),
            ('Vendas em Andamento', '#fd7e14', 3),
            ('Vendas Concluídas', '#28a745', 4),
            ('Pós-venda', '#6f42c1', 5)
        ]
        
        for name, color, position in default_columns:
            column = KanbanColumn(name=name, color=color, order_position=position)
            db.session.add(column)
        
        db.session.commit()
    
    columns = KanbanColumn.query.filter_by(active=True).order_by(KanbanColumn.order_position).all()
    clients = Client.query.all()
    users = User.query.filter_by(active=True).all()
    
    return render_template('kanban.html', columns=columns, clients=clients, users=users)

@app.route('/kanban/card', methods=['POST'])
@login_required
def create_kanban_card():
    form = KanbanCardForm()
    form.client_id.choices = [(0, 'Selecionar cliente...')] + [(c.id, c.name) for c in Client.query.all()]
    form.responsible_id.choices = [(0, 'Selecionar responsável...')] + [(u.id, u.name) for u in User.query.filter_by(active=True).all()]
    
    if form.validate_on_submit():
        # Get the column and calculate position
        column_id = request.form.get('column_id', type=int)
        max_position = db.session.query(db.func.max(KanbanCard.order_position)).filter_by(column_id=column_id).scalar() or 0
        
        card = KanbanCard(
            title=form.title.data,
            description=form.description.data,
            client_id=form.client_id.data if form.client_id.data != 0 else None,
            column_id=column_id,
            responsible_id=form.responsible_id.data if form.responsible_id.data != 0 else None,
            priority=form.priority.data,
            due_date=form.due_date.data,
            order_position=max_position + 1
        )
        
        db.session.add(card)
        db.session.commit()
        
        log_activity('kanban_card_created', f'Cartão criado: {card.title}')
        
        return jsonify({'success': True, 'card_id': card.id})
    
    return jsonify({'success': False, 'errors': form.errors})

@app.route('/kanban/card/<int:card_id>/move', methods=['POST'])
@login_required
def move_kanban_card(card_id):
    card = KanbanCard.query.get_or_404(card_id)
    new_column_id = request.json.get('column_id')
    new_position = request.json.get('position', 1)
    
    # Update other cards positions in the new column
    cards_in_column = KanbanCard.query.filter_by(column_id=new_column_id).filter(
        KanbanCard.id != card_id
    ).order_by(KanbanCard.order_position).all()
    
    for i, other_card in enumerate(cards_in_column):
        if i >= new_position - 1:
            other_card.order_position = i + 2
        else:
            other_card.order_position = i + 1
    
    card.column_id = new_column_id
    card.order_position = new_position
    
    db.session.commit()
    
    log_activity('kanban_card_moved', f'Cartão movido: {card.title}')
    
    return jsonify({'success': True})

@app.route('/clients')
@login_required
def clients():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Client.query
    
    if search:
        query = query.filter(
            db.or_(
                Client.name.ilike(f'%{search}%'),
                Client.email.ilike(f'%{search}%'),
                Client.phone.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    clients = query.order_by(Client.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('clients.html', clients=clients, search=search, status_filter=status_filter)

@app.route('/clients/new', methods=['GET', 'POST'])
@login_required
def new_client():
    form = ClientForm()
    
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            whatsapp=form.whatsapp.data,
            cpf_cnpj=form.cpf_cnpj.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            birth_date=form.birth_date.data,
            insurance_type=form.insurance_type.data,
            notes=form.notes.data,
            status=form.status.data
        )
        
        db.session.add(client)
        db.session.commit()
        
        log_activity('client_created', f'Cliente criado: {client.name}')
        flash('Cliente criado com sucesso!', 'success')
        return redirect(url_for('clients'))
    
    return render_template('client_form.html', form=form, title='Novo Cliente')

@app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client)
    
    if form.validate_on_submit():
        form.populate_obj(client)
        client.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_activity('client_updated', f'Cliente atualizado: {client.name}')
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('clients'))
    
    return render_template('client_form.html', form=form, title='Editar Cliente', client=client)

@app.route('/whatsapp')
@login_required
def whatsapp():
    messages = whatsapp_service.get_messages()
    clients = Client.query.filter(Client.whatsapp.isnot(None)).all()
    
    return render_template('whatsapp.html', messages=messages, clients=clients)

@app.route('/whatsapp/send', methods=['POST'])
@login_required
def send_whatsapp():
    form = WhatsAppMessageForm()
    
    if form.validate_on_submit():
        result = whatsapp_service.send_message(form.phone_number.data, form.message.data)
        
        if result:
            log_activity('whatsapp_sent', f'Mensagem enviada para {form.phone_number.data}')
            flash('Mensagem enviada com sucesso!', 'success')
        else:
            flash('Erro ao enviar mensagem. Verifique a configuração do WhatsApp.', 'danger')
    
    return redirect(url_for('whatsapp'))

@app.route('/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    if request.method == 'GET':
        # Webhook verification
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # You should verify the token here
        if verify_token == 'your_verify_token':
            return challenge
        else:
            return 'Invalid verify token', 403
    
    elif request.method == 'POST':
        # Process incoming messages
        whatsapp_service.process_incoming_message(request.json)
        return 'OK', 200

@app.route('/users')
@login_required
def users():
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem gerenciar usuários.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users)

@app.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem criar usuários.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = UserForm()
    
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            db.or_(User.username == form.username.data, User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Usuário ou email já existem.', 'danger')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                name=form.name.data,
                password_hash=generate_password_hash(form.password.data),
                role=form.role.data,
                active=form.active.data
            )
            
            db.session.add(user)
            db.session.commit()
            
            log_activity('user_created', f'Usuário criado: {user.username}')
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('users'))
    
    return render_template('user_form.html', form=form, title='Novo Usuário')

@app.route('/api/kanban/cards')
@login_required
def api_kanban_cards():
    cards = KanbanCard.query.all()
    return jsonify([{
        'id': card.id,
        'title': card.title,
        'description': card.description,
        'client_name': card.client.name if card.client else None,
        'responsible_name': card.responsible_user.name if card.responsible_user else None,
        'priority': card.priority,
        'due_date': card.due_date.isoformat() if card.due_date else None,
        'column_id': card.column_id,
        'order_position': card.order_position
    } for card in cards])

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
