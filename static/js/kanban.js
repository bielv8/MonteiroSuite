// Kanban Board JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeKanban();
    initializeCardForm();
});

function initializeKanban() {
    // Initialize SortableJS for each kanban column
    const columns = document.querySelectorAll('.kanban-cards');
    
    columns.forEach(column => {
        new Sortable(column, {
            group: 'kanban-cards',
            animation: 150,
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            dragClass: 'sortable-drag',
            onEnd: function(evt) {
                handleCardMove(evt);
            }
        });
    });
}

function initializeCardForm() {
    const form = document.getElementById('addCardForm');
    const modal = document.getElementById('addCardModal');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            createKanbanCard();
        });
    }
    
    // Handle add card buttons for each column
    document.querySelectorAll('.kanban-column-header').forEach(header => {
        const addButton = document.createElement('button');
        addButton.className = 'btn btn-sm btn-outline-primary';
        addButton.innerHTML = '<i class="fas fa-plus"></i>';
        addButton.title = 'Adicionar cartão';
        addButton.onclick = function() {
            const columnId = header.closest('.kanban-column').getAttribute('data-column-id');
            openAddCardModal(columnId);
        };
        
        const badgeContainer = header.querySelector('.badge').parentNode;
        badgeContainer.appendChild(addButton);
    });
}

function openAddCardModal(columnId) {
    document.getElementById('column_id').value = columnId;
    
    // Reset form
    document.getElementById('addCardForm').reset();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addCardModal'));
    modal.show();
}

function createKanbanCard() {
    const form = document.getElementById('addCardForm');
    const formData = new FormData(form);
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Criando...';
    submitBtn.disabled = true;
    
    fetch('/kanban/card', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal and reload page to show new card
            const modal = bootstrap.Modal.getInstance(document.getElementById('addCardModal'));
            modal.hide();
            location.reload();
        } else {
            // Show errors
            showFormErrors(data.errors);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Erro ao criar cartão. Tente novamente.', 'danger');
    })
    .finally(() => {
        // Reset button state
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

function handleCardMove(evt) {
    const cardId = evt.item.getAttribute('data-card-id');
    const newColumnId = evt.to.getAttribute('data-column-id');
    const newPosition = evt.newIndex + 1;
    
    // Show loading indicator on the card
    const card = evt.item;
    card.style.opacity = '0.7';
    
    fetch(`/kanban/card/${cardId}/move`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            column_id: parseInt(newColumnId),
            position: newPosition
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update column badges
            updateColumnBadges();
            showAlert('Cartão movido com sucesso!', 'success');
        } else {
            // Revert the move
            evt.from.insertBefore(evt.item, evt.from.children[evt.oldIndex]);
            showAlert('Erro ao mover cartão. Tente novamente.', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Revert the move
        evt.from.insertBefore(evt.item, evt.from.children[evt.oldIndex]);
        showAlert('Erro ao mover cartão. Tente novamente.', 'danger');
    })
    .finally(() => {
        // Remove loading indicator
        card.style.opacity = '1';
    });
}

function updateColumnBadges() {
    document.querySelectorAll('.kanban-column').forEach(column => {
        const badge = column.querySelector('.badge');
        const cardCount = column.querySelectorAll('.kanban-card').length;
        badge.textContent = cardCount;
    });
}

function showFormErrors(errors) {
    // Clear previous errors
    document.querySelectorAll('.text-danger').forEach(el => el.remove());
    
    // Show new errors
    Object.keys(errors).forEach(fieldName => {
        const field = document.querySelector(`[name="${fieldName}"]`);
        if (field) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-danger small mt-1';
            errorDiv.textContent = errors[fieldName][0];
            field.parentNode.appendChild(errorDiv);
        }
    });
}

function showAlert(message, type) {
    const alertContainer = document.querySelector('.container-fluid');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alert, alertContainer.firstChild);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 3000);
}

// Card detail modal functionality
function showCardDetails(cardId) {
    // Fetch card details and show in modal
    fetch(`/api/kanban/cards/${cardId}`)
    .then(response => response.json())
    .then(data => {
        // Create and show card details modal
        createCardDetailsModal(data);
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Erro ao carregar detalhes do cartão.', 'danger');
    });
}

function createCardDetailsModal(cardData) {
    // Create modal HTML dynamically
    const modalHTML = `
        <div class="modal fade" id="cardDetailsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${cardData.title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-8">
                                <h6>Descrição</h6>
                                <p>${cardData.description || 'Nenhuma descrição'}</p>
                                
                                <h6>Cliente</h6>
                                <p>${cardData.client_name || 'Não informado'}</p>
                                
                                <h6>Responsável</h6>
                                <p>${cardData.responsible_name || 'Não informado'}</p>
                            </div>
                            <div class="col-md-4">
                                <h6>Prioridade</h6>
                                <span class="badge priority-${cardData.priority}">${cardData.priority}</span>
                                
                                <h6 class="mt-3">Data de Vencimento</h6>
                                <p>${cardData.due_date || 'Não informado'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        <button type="button" class="btn btn-primary" onclick="editCard(${cardData.id})">Editar</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('cardDetailsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM and show
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    const modal = new bootstrap.Modal(document.getElementById('cardDetailsModal'));
    modal.show();
}

function editCard(cardId) {
    // Close details modal and open edit modal
    const detailsModal = bootstrap.Modal.getInstance(document.getElementById('cardDetailsModal'));
    detailsModal.hide();
    
    // For now, redirect to edit page or implement inline editing
    console.log('Edit card:', cardId);
}

// Add click handlers to existing cards
document.addEventListener('click', function(e) {
    if (e.target.closest('.kanban-card')) {
        const card = e.target.closest('.kanban-card');
        const cardId = card.getAttribute('data-card-id');
        
        // Don't trigger on drag operations
        if (!card.classList.contains('sortable-chosen')) {
            showCardDetails(cardId);
        }
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Press 'N' to create new card in first column
    if (e.key === 'n' || e.key === 'N') {
        if (!e.target.matches('input, textarea, select')) {
            e.preventDefault();
            const firstColumn = document.querySelector('.kanban-column');
            if (firstColumn) {
                const columnId = firstColumn.getAttribute('data-column-id');
                openAddCardModal(columnId);
            }
        }
    }
    
    // Press 'Escape' to close modals
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Auto-refresh kanban every 30 seconds
setInterval(function() {
    // Only refresh if no modals are open and no drag operation is happening
    const openModals = document.querySelectorAll('.modal.show');
    const dragOperation = document.querySelector('.sortable-chosen');
    
    if (openModals.length === 0 && !dragOperation) {
        // Soft refresh - just update the badges
        updateColumnBadges();
    }
}, 30000);

