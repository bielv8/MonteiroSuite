// Servidor personalizado para integração com Monteiro Corretora
const express = require('express');
const cors = require('cors');
const config = require('./config-custom.js');

// Importar funções dos controladores do WPPConnect
const { 
  startSession, 
  closeSession, 
  getSessionState, 
  getQrCode 
} = require('./dist/controller/sessionController');

const { 
  sendMessage, 
  sendImage, 
  sendFile, 
  sendFileFromBase64, 
  sendVoice,
  sendLocation,
  sendLinkPreview,
  sendContactVcard,
  sendButtons,
  sendListMenu
} = require('./dist/controller/messageController');

const { 
  createGroup, 
  addParticipant, 
  removeParticipant, 
  promoteParticipant,
  demoteParticipant,
  getGroupMembers,
  getGroupAdmins,
  getGroupInviteLink
} = require('./dist/controller/groupController');

const { 
  getAllContacts, 
  getAllChats, 
  getAllGroups, 
  getBatteryLevel 
} = require('./dist/controller/deviceController');

const app = express();

// Middlewares
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Middleware de autenticação personalizado
app.use('/api', (req, res, next) => {
  const authHeader = req.headers.authorization;
  const expectedToken = `Bearer ${config.secretKey}`;
  
  if (!authHeader || authHeader !== expectedToken) {
    return res.status(401).json({ 
      error: 'Acesso negado. Token de autenticação inválido.' 
    });
  }
  
  next();
});

// Rotas de sessão
app.post('/api/:session/start-session', startSession);
app.post('/api/:session/close-session', closeSession);
app.get('/api/:session/status-session', getSessionState);
app.get('/api/:session/qrcode-session', getQrCode);

// Rotas de mensagens
app.post('/api/:session/send-message', sendMessage);
app.post('/api/:session/send-image', sendImage);
app.post('/api/:session/send-file', sendFile);
app.post('/api/:session/send-file-base64', sendFileFromBase64);
app.post('/api/:session/send-voice', sendVoice);
app.post('/api/:session/send-location', sendLocation);
app.post('/api/:session/send-link-preview', sendLinkPreview);
app.post('/api/:session/send-contact-vcard', sendContactVcard);
app.post('/api/:session/send-buttons', sendButtons);
app.post('/api/:session/send-list-menu', sendListMenu);

// Rotas de grupos
app.post('/api/:session/create-group', createGroup);
app.post('/api/:session/add-participant-group', addParticipant);
app.post('/api/:session/remove-participant-group', removeParticipant);
app.post('/api/:session/promote-participant-group', promoteParticipant);
app.post('/api/:session/demote-participant-group', demoteParticipant);
app.get('/api/:session/group-members/:groupId', getGroupMembers);
app.get('/api/:session/group-admins/:groupId', getGroupAdmins);
app.get('/api/:session/group-invite-link/:groupId', getGroupInviteLink);

// Rotas de contatos e dispositivos
app.get('/api/:session/all-contacts', getAllContacts);
app.get('/api/:session/all-chats', getAllChats);
app.get('/api/:session/all-groups', getAllGroups);
app.get('/api/:session/battery-level', getBatteryLevel);

// Rota de status da API
app.get('/api/status', (req, res) => {
  res.json({
    status: 'online',
    message: 'WPPConnect Server para Monteiro Corretora está funcionando',
    timestamp: new Date().toISOString(),
    version: '2.8.6-monteiro'
  });
});

// Rota de healthcheck
app.get('/healthcheck', (req, res) => {
  res.json({ status: 'ok', service: 'wppconnect-monteiro' });
});

// Middleware de tratamento de erros
app.use((err, req, res, next) => {
  console.error('Erro no WPPConnect Server:', err);
  res.status(500).json({
    error: 'Erro interno do servidor',
    message: err.message,
    timestamp: new Date().toISOString()
  });
});

// Iniciar servidor
const PORT = config.port;
const HOST = config.host;

app.listen(PORT, HOST, () => {
  console.log(`🚀 WPPConnect Server para Monteiro Corretora rodando em ${HOST}:${PORT}`);
  console.log(`📱 Configurado para funcionar com sistema Flask`);
  console.log(`🔐 Token de autenticação: ${config.secretKey}`);
});

module.exports = app;