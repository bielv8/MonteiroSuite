// Servidor WPPConnect simplificado para Monteiro Corretora
const express = require('express');
const cors = require('cors');
const config = require('./config-custom.js');

// Importar apenas as funções essenciais
const { 
  startSession, 
  closeSession, 
  getSessionState, 
  getQrCode 
} = require('./dist/controller/sessionController');

const { 
  sendMessage
} = require('./dist/controller/messageController');

const app = express();

// Middlewares básicos
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Middleware de autenticação simplificado
app.use('/api', (req, res, next) => {
  const authHeader = req.headers.authorization;
  const expectedToken = `Bearer ${config.secretKey}`;
  
  if (!authHeader || authHeader !== expectedToken) {
    return res.status(401).json({ 
      error: 'Token inválido',
      success: false
    });
  }
  
  next();
});

// Rotas essenciais de sessão
app.post('/api/:session/start-session', (req, res, next) => {
  console.log('Iniciando sessão:', req.params.session);
  startSession(req, res, next);
});

app.post('/api/:session/close-session', (req, res, next) => {
  console.log('Fechando sessão:', req.params.session);
  closeSession(req, res, next);
});

app.get('/api/:session/status-session', (req, res, next) => {
  console.log('Verificando status da sessão:', req.params.session);
  getSessionState(req, res, next);
});

app.get('/api/:session/qrcode-session', (req, res, next) => {
  console.log('Obtendo QR Code para sessão:', req.params.session);
  getQrCode(req, res, next);
});

// Rota básica de mensagem
app.post('/api/:session/send-message', (req, res, next) => {
  console.log('Enviando mensagem na sessão:', req.params.session);
  sendMessage(req, res, next);
});

// Rota de status da API
app.get('/api/status', (req, res) => {
  res.json({
    status: 'online',
    message: 'WPPConnect Server Simplificado para Monteiro Corretora',
    timestamp: new Date().toISOString(),
    version: '2.8.6-monteiro-simple'
  });
});

// Rota de healthcheck
app.get('/healthcheck', (req, res) => {
  res.json({ status: 'ok', service: 'wppconnect-monteiro-simple' });
});

// Middleware de tratamento de erros
app.use((err, req, res, next) => {
  console.error('Erro no WPPConnect Server:', err);
  res.status(500).json({
    error: 'Erro interno do servidor',
    message: err.message,
    success: false,
    timestamp: new Date().toISOString()
  });
});

// Iniciar servidor
const PORT = config.port;
const HOST = config.host;

app.listen(PORT, HOST, () => {
  console.log(`🚀 WPPConnect Server Simplificado rodando em ${HOST}:${PORT}`);
  console.log(`📱 Configurado para Monteiro Corretora`);
  console.log(`🔐 Token: ${config.secretKey}`);
  console.log(`ℹ️  Teste a API com: GET ${HOST}:${PORT}/api/status`);
});

module.exports = app;