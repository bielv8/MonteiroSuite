// Servidor personalizado para integração com Monteiro Corretora
const express = require('express');
const cors = require('cors');
const config = require('./config-custom.js');

// Importar controladores do WPPConnect
const sessionController = require('./dist/controller/sessionController');
const messageController = require('./dist/controller/messageController');
const groupController = require('./dist/controller/groupController');
const deviceController = require('./dist/controller/deviceController');

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
app.post('/api/:session/start-session', sessionController.start);
app.post('/api/:session/close-session', sessionController.close);
app.get('/api/:session/status-session', sessionController.status);
app.get('/api/:session/qrcode-session', sessionController.qrcode);

// Rotas de mensagens
app.post('/api/:session/send-message', messageController.sendMessage);
app.post('/api/:session/send-image', messageController.sendImage);
app.post('/api/:session/send-file', messageController.sendFile);
app.post('/api/:session/send-file-base64', messageController.sendFileFromBase64);
app.post('/api/:session/send-voice', messageController.sendVoice);
app.post('/api/:session/send-location', messageController.sendLocation);
app.post('/api/:session/send-link-preview', messageController.sendLinkPreview);
app.post('/api/:session/send-contact-vcard', messageController.sendContactVcard);
app.post('/api/:session/send-buttons', messageController.sendButtons);
app.post('/api/:session/send-list-menu', messageController.sendListMenu);

// Rotas de grupos
app.post('/api/:session/create-group', groupController.createGroup);
app.post('/api/:session/add-participant-group', groupController.addParticipant);
app.post('/api/:session/remove-participant-group', groupController.removeParticipant);
app.post('/api/:session/promote-participant-group', groupController.promoteParticipant);
app.post('/api/:session/demote-participant-group', groupController.demoteParticipant);
app.get('/api/:session/group-members/:groupId', groupController.getGroupMembers);
app.get('/api/:session/group-admins/:groupId', groupController.getGroupAdmins);
app.get('/api/:session/group-invite-link/:groupId', groupController.getGroupInviteLink);

// Rotas de contatos e dispositivos
app.get('/api/:session/all-contacts', deviceController.getAllContacts);
app.get('/api/:session/all-chats', deviceController.getAllChats);
app.get('/api/:session/all-groups', deviceController.getAllGroups);
app.get('/api/:session/battery-level', deviceController.getBatteryLevel);

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