// config.js
// Centralização da URL da API do DengueCare para suportar desenvolvimento local e produção no Render

export const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api/v1'
    : 'https://denguecare.onrender.com/api/v1'; // Ajustado para corresponder ao nome do serviço 'DengueCare' no Render
