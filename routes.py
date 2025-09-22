from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
import logging

from app import app, db
from models import User, Client, KanbanColumn, KanbanCard
from forms import LoginForm, ClientForm, KanbanCardForm, UserForm
from whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)

def log_activity(action, description=None):
    """Simplified logging - removed to optimize resources"""
    pass

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
        
        if user and user.password_hash and form.password.data and check_password_hash(user.password_hash, form.password.data):
            if user.active:
                login_user(user, remember=form.remember_me.data)
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
    
    # Get kanban statistics
    kanban_stats = {}
    columns = KanbanColumn.query.filter_by(active=True).order_by(KanbanColumn.order_position).all()
    for column in columns:
        kanban_stats[column.name] = KanbanCard.query.filter_by(column_id=column.id).count()
    
    total_cards = KanbanCard.query.count()
    
    # Get WhatsApp status for dashboard
    try:
        whatsapp_status = whatsapp_service.get_session_status()
        whatsapp_connected = whatsapp_service.is_connected()
        qr_code = None
        if not whatsapp_connected:
            qr_response = whatsapp_service.get_qr_code()
            qr_code = qr_response.get('qrcode') if qr_response.get('success') else None
    except Exception as e:
        logger.error(f"Erro ao verificar status do WhatsApp: {e}")
        whatsapp_status = {"error": str(e)}
        whatsapp_connected = False
        qr_code = None
    
    # Get recent clients for WhatsApp quick access
    recent_clients = Client.query.filter(Client.phone.isnot(None)).order_by(Client.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                         total_clients=total_clients,
                         active_clients=active_clients,
                         prospects=prospects,
                         kanban_stats=kanban_stats,
                         total_cards=total_cards,
                         whatsapp_status=whatsapp_status,
                         whatsapp_connected=whatsapp_connected,
                         qr_code=qr_code,
                         recent_clients=recent_clients)

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
            column = KanbanColumn()
            column.name = name
            column.color = color
            column.order_position = position
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
    clients = Client.query.all()
    form.client_id.choices = [('0', 'Selecionar cliente...')] + [(str(c.id), c.name) for c in clients]  # type: ignore
    
    if form.validate_on_submit():
        # Get the column and calculate position
        column_id = request.form.get('column_id', type=int)
        max_position = db.session.query(db.func.max(KanbanCard.order_position)).filter_by(column_id=column_id).scalar() or 0
        
        card = KanbanCard()
        card.title = form.title.data
        card.description = form.description.data
        card.client_id = int(form.client_id.data) if form.client_id.data != '0' else None
        card.column_id = column_id
        card.priority = form.priority.data
        card.order_position = max_position + 1
        
        db.session.add(card)
        db.session.commit()
        
        log_activity('kanban_card_created', f'Cartão criado: {card.title}')
        
        return jsonify({'success': True, 'card_id': card.id})
    
    return jsonify({'success': False, 'errors': form.errors})

@app.route('/kanban/card/<int:card_id>/move', methods=['POST'])
@login_required
def move_kanban_card(card_id):
    card = KanbanCard.query.get_or_404(card_id)
    data = request.get_json()
    new_column_id = data.get('column_id') if data else None
    new_position = data.get('position', 1) if data else 1
    
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
        client = Client()
        client.name = form.name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.insurance_type = form.insurance_type.data
        client.notes = form.notes.data
        client.status = form.status.data
        
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

# WhatsApp funcionalidade removida para otimização

@app.route('/users')
@login_required
def users():
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem gerenciar usuários.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users)

# ==================== ROTAS DO WHATSAPP ====================

@app.route('/whatsapp')
@login_required
def whatsapp():
    """Página principal do WhatsApp"""
    # Verificar status da conexão
    status = whatsapp_service.get_session_status()
    is_connected = whatsapp_service.is_connected()
    
    # Obter QR Code se não estiver conectado
    qr_code = None
    if not is_connected:
        qr_response = whatsapp_service.get_qr_code()
        qr_raw = qr_response.get('qrcode') if qr_response.get('success') else None
        # Normalizar QR code - remover prefixo se já existir
        if qr_raw and qr_raw.startswith('data:image'):
            qr_code = qr_raw.split(',', 1)[1] if ',' in qr_raw else qr_raw
        else:
            qr_code = qr_raw
    
    # Obter dados necessários para o template
    clients = Client.query.filter(Client.phone.isnot(None)).order_by(Client.name).all()
    
    return render_template('whatsapp.html', 
                         status=status, 
                         is_connected=is_connected,
                         qr_code=qr_code,
                         clients=clients,
                         messages=[])

@app.route('/whatsapp/start-session', methods=['POST'])
@login_required
def start_whatsapp_session():
    """Inicia uma nova sessão do WhatsApp"""
    try:
        result = whatsapp_service.start_session()
        if result.get('success', True):
            flash('Sessão do WhatsApp iniciada com sucesso!', 'success')
            log_activity('whatsapp_session_start', 'Sessão do WhatsApp iniciada')
        else:
            flash(f'Erro ao iniciar sessão: {result.get("message", "Erro desconhecido")}', 'error')
    except Exception as e:
        flash(f'Erro ao conectar com o WhatsApp: {str(e)}', 'error')
        logger.error(f"Erro ao iniciar sessão WhatsApp: {e}")
    
    return redirect(url_for('whatsapp'))

@app.route('/whatsapp/close-session', methods=['POST'])
@login_required
def close_whatsapp_session():
    """Fecha a sessão atual do WhatsApp"""
    try:
        result = whatsapp_service.close_session()
        if result.get('success', True):
            flash('Sessão do WhatsApp encerrada com sucesso!', 'info')
            log_activity('whatsapp_session_close', 'Sessão do WhatsApp encerrada')
        else:
            flash(f'Erro ao encerrar sessão: {result.get("message", "Erro desconhecido")}', 'error')
    except Exception as e:
        flash(f'Erro ao desconectar do WhatsApp: {str(e)}', 'error')
        logger.error(f"Erro ao encerrar sessão WhatsApp: {e}")
    
    return redirect(url_for('whatsapp'))

@app.route('/whatsapp/status', methods=['GET'])
@login_required
def whatsapp_status():
    """API para verificar status do WhatsApp"""
    try:
        status = whatsapp_service.get_session_status()
        is_connected = whatsapp_service.is_connected()
        health = whatsapp_service.health_check()
        
        return jsonify({
            'connected': is_connected,
            'status': status,
            'health': health,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'connected': False,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/whatsapp/send-message', methods=['POST'])
@login_required
def send_whatsapp_message():
    """Envia uma mensagem via WhatsApp"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        message = data.get('message')
        
        if not phone or not message:
            return jsonify({'error': 'Telefone e mensagem são obrigatórios'}), 400
        
        result = whatsapp_service.send_text_message(phone, message)
        
        if result.get('success', True):
            log_activity('whatsapp_message_sent', f'Mensagem enviada para {phone}')
            return jsonify({'success': True, 'result': result})
        else:
            return jsonify({'error': result.get('message', 'Erro ao enviar mensagem')}), 500
            
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/whatsapp/contacts', methods=['GET'])
@login_required
def get_whatsapp_contacts():
    """Obtém lista de contatos do WhatsApp"""
    try:
        contacts = whatsapp_service.get_all_contacts()
        return jsonify(contacts)
    except Exception as e:
        logger.error(f"Erro ao obter contatos WhatsApp: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/whatsapp/chats', methods=['GET'])
@login_required
def get_whatsapp_chats():
    """Obtém lista de conversas do WhatsApp"""
    try:
        chats = whatsapp_service.get_all_chats()
        return jsonify(chats)
    except Exception as e:
        logger.error(f"Erro ao obter conversas WhatsApp: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/client/<int:client_id>/send-whatsapp', methods=['POST'])
@login_required
def send_whatsapp_to_client(client_id):
    """Envia mensagem WhatsApp para um cliente específico"""
    try:
        client = Client.query.get_or_404(client_id)
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400
        
        if not client.phone:
            return jsonify({'error': 'Cliente não possui telefone cadastrado'}), 400
        
        result = whatsapp_service.send_text_message(client.phone, message)
        
        if result.get('success', True):
            log_activity('client_whatsapp_sent', f'WhatsApp enviado para cliente {client.name}')
            return jsonify({'success': True, 'result': result})
        else:
            return jsonify({'error': result.get('message', 'Erro ao enviar mensagem')}), 500
            
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp para cliente {client_id}: {e}")
        return jsonify({'error': str(e)}), 500

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
            if not form.password.data:
                flash('Senha é obrigatória para novos usuários.', 'danger')
                return render_template('user_form.html', form=form, title='Novo Usuário')
                
            user = User()
            user.username = form.username.data
            user.email = form.email.data
            user.name = form.name.data
            user.password_hash = generate_password_hash(form.password.data)
            user.role = form.role.data
            user.active = form.active.data
            
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

# API routes simplificadas

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem editar usuários.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        # Check if username or email already exists (excluding current user)
        existing_user = User.query.filter(
            db.or_(User.username == form.username.data, User.email == form.email.data),
            User.id != user_id
        ).first()
        
        if existing_user:
            flash('Usuário ou email já existem.', 'danger')
        else:
            user.username = form.username.data
            user.email = form.email.data
            user.name = form.name.data
            user.role = form.role.data
            user.active = form.active.data
            
            # Only update password if provided
            if form.password.data:
                user.password_hash = generate_password_hash(form.password.data)
            
            db.session.commit()
            
            log_activity('user_updated', f'Usuário atualizado: {user.username}')
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('users'))
    
    return render_template('user_form.html', form=form, title='Editar Usuário', user=user)

@app.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Acesso negado'})
    
    user = User.query.get_or_404(user_id)
    user.active = not user.active
    db.session.commit()
    
    action = 'ativado' if user.active else 'desativado'
    log_activity('user_status_changed', f'Usuário {action}: {user.username}')
    
    return jsonify({'success': True})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
