/**
 * MTG Camera Translator & Card Finder
 *
 * Aplicação principal que orquestra o fluxo:
 * 1. Captura de imagem (CameraCapture)
 * 2. Envio para o backend (api.js)
 * 3. Exibição do resultado (CardResult)
 *
 * Estados:
 * - idle: Aguardando imagem
 * - loading: Processando identificação
 * - success: Carta identificada
 * - not_identified: IA não conseguiu identificar
 * - error: Erro no processo
 */
import { useState, useCallback } from 'react';
import CameraCapture from '../components/CameraCapture';
import CardResult from '../components/CardResult';
import LoadingOverlay from '../components/LoadingOverlay';
import ErrorMessage from '../components/ErrorMessage';
import PaywallModal from '../components/PaywallModal';
import { identifyCard } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import icones from '../imagem/icones.png';
import logoImg from '../imagem/logo.svg.png';
import instaIcon from '../imagem/instagran.png';
import DownloadApp from '../components/DownloadApp';

export default function Home() {
  const { username, logout } = useAuth();
  const navigate = useNavigate();
  const [state, setState] = useState('idle'); // idle | loading | success | not_identified | error
  const [selectedFile, setSelectedFile] = useState(null);
  const [cardData, setCardData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [notIdentifiedMessage, setNotIdentifiedMessage] = useState('');
  const [showPaywall, setShowPaywall] = useState(false);

  /**
   * Callback quando o usuário seleciona uma imagem.
   */
  const handleCapture = useCallback((file) => {
    setSelectedFile(file);
    // Reset estado se remover imagem
    if (!file) {
      setState('idle');
      setCardData(null);
      setErrorMessage('');
      setNotIdentifiedMessage('');
    }
  }, []);

  /**
   * Envia a imagem para identificação no backend.
   */
  const handleIdentify = async () => {
    if (!selectedFile) return;

    setState('loading');
    setCardData(null);
    setErrorMessage('');
    setNotIdentifiedMessage('');

    try {
      const response = await identifyCard(selectedFile);

      if (response.identified && response.card) {
        setCardData(response.card);
        setState('success');
      } else {
        setNotIdentifiedMessage(
          response.message ||
          'Não foi possível identificar a carta. Tente uma foto mais nítida.'
        );
        setState('not_identified');
      }
    } catch (error) {
      if (error.message === 'LIMIT_REACHED') {
        setShowPaywall(true);
        setState('idle');
      } else {
        setErrorMessage(error.message || 'Erro ao processar a imagem.');
        setState('error');
      }
    }
  };

  /**
   * Reseta tudo para o estado inicial.
   */
  const handleReset = () => {
    setState('idle');
    setSelectedFile(null);
    setCardData(null);
    setErrorMessage('');
    setNotIdentifiedMessage('');
  };

  return (
    <div className="app">
      <PaywallModal isOpen={showPaywall} onClose={() => setShowPaywall(false)} />

      {/* Barra de usuário logado no topo */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 20px', backgroundColor: 'rgba(0,0,0,0.5)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
          Logado como <strong style={{ color: 'var(--color-gold)' }}>{username}</strong>
        </span>
        <button 
          onClick={() => { logout(); navigate('/login'); }}
          style={{ background: 'none', border: 'none', color: '#ff4444', cursor: 'pointer', fontWeight: 'bold' }}
        >
          Sair
        </button>
      </div>

      {/* Header */}
      <header className="app-header" style={{ marginBottom: '1rem' }}>
        <div className="app-header__icon">
          <img 
            src={icones} 
            alt="Ícone Mana MTG" 
            style={{ width: '400px', maxWidth: '100%', height: 'auto', objectFit: 'contain', filter: 'drop-shadow(0 0 20px rgba(212, 168, 67, 0.5))' }} 
          />
        </div>
        
        {/* Logo que substituiu o texto MTG tradutor */}
        <div className="app-header__logo" style={{ marginTop: '-40px', marginBottom: '-20px' }}>
          <img 
            src={logoImg} 
            alt="Logo Magic" 
            style={{ width: '300px', maxWidth: '100%', height: 'auto', objectFit: 'contain' }} 
          />
        </div>
        
        <p className="app-header__subtitle" style={{ fontSize: '1.2rem', margin: '0', fontWeight: '500', letterSpacing: '0.05em', position: 'relative', zIndex: 10 }}>
          Tradutor de cards
        </p>
      </header>

      {/* Área principal */}
      <main>
        {state === 'loading' ? (
          /* Estado: Carregando */
          <div className="glass-card">
            <LoadingOverlay />
          </div>
        ) : state === 'success' && cardData ? (
          /* Estado: Carta identificada */
          <>
            <CardResult card={cardData} />
            <div style={{ marginTop: '1.5rem', width: '100%', maxWidth: 480 }}>
              <button
                className="btn btn--secondary btn--full"
                onClick={handleReset}
                id="btn-scan-again"
              >
                🔄 Escanear outra carta
              </button>
            </div>
          </>
        ) : state === 'not_identified' ? (
          /* Estado: Carta não identificada */
          <div className="glass-card">
            <div className="not-identified">
              <div className="not-identified__icon">🔍</div>
              <h2 className="not-identified__title">Carta não identificada</h2>
              <p className="not-identified__message">{notIdentifiedMessage}</p>
              <button
                className="btn btn--primary"
                onClick={handleReset}
                style={{ marginTop: '1.5rem' }}
                id="btn-try-again"
              >
                Tentar novamente
              </button>
            </div>
          </div>
        ) : (
          /* Estado: Idle / Erro */
          <div className="glass-card">
            <CameraCapture
              onCapture={handleCapture}
              disabled={state === 'loading'}
            />

            {/* Erro */}
            {state === 'error' && (
              <div style={{ marginTop: '1rem' }}>
                <ErrorMessage
                  message={errorMessage}
                  onDismiss={() => {
                    setState('idle');
                    setErrorMessage('');
                  }}
                />
              </div>
            )}

            {/* Botão de identificação */}
            {selectedFile && state !== 'error' && (
              <button
                className="btn btn--primary btn--full"
                onClick={handleIdentify}
                disabled={state === 'loading'}
                style={{ marginTop: '1.5rem' }}
                id="btn-identify"
              >
                {state === 'loading' ? (
                  <>
                    <span className="btn__spinner" />
                    Identificando...
                  </>
                ) : (
                  '✨ Identificar Carta'
                )}
              </button>
            )}
          </div>
        )}
      </main>

      {/* Componente de Download (Native App) */}
      <DownloadApp />

      {/* Footer */}
      <footer className="app-header__subtitle" style={{ marginTop: 'auto', padding: '2rem 0 1rem', textAlign: 'center', fontSize: '0.85rem' }}>
        
        {/* Bloco de Parceiros */}
        <div style={{ marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.9rem', color: 'var(--color-gold)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 'bold' }}>
            Parceiros Oficiais
          </span>
          
          <div style={{ display: 'flex', flexDirection: 'row', gap: '1.5rem', flexWrap: 'wrap', justifyContent: 'center', marginTop: '10px' }}>
            {[
              { id: 1, name: '@luciano.saints', link: 'https://instagram.com/luciano.saints' },
              { id: 2, name: '@parceiro_2', link: '#' },
              { id: 3, name: '@parceiro_3', link: '#' },
              { id: 4, name: '@parceiro_4', link: '#' },
              { id: 5, name: '@parceiro_5', link: '#' },
              { id: 6, name: '@parceiro_6', link: '#' },
              { id: 7, name: '@parceiro_7', link: '#' },
            ].map((partner) => (
              <a 
                key={partner.id}
                href={partner.link} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textDecoration: 'none', transition: 'transform 0.2s' }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.15)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
              >
                <img 
                  src={instaIcon} 
                  alt={`Instagram ${partner.name}`} 
                  style={{ width: '40px', height: '40px', objectFit: 'contain', filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.5))' }} 
                />
                <span style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontWeight: partner.id === 1 ? 'bold' : 'normal' }}>
                  {partner.name}
                </span>
              </a>
            ))}
          </div>
        </div>

        <p>
          Dados de cartas por{' '}
          <a href="https://scryfall.com" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-purple-light)' }}>
            Scryfall
          </a>{' '}
          • IA de visão por{' '}
          <a href="https://openrouter.ai" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-purple-light)' }}>
            OpenRouter
          </a>
        </p>
        <p style={{ marginTop: '0.5rem', fontWeight: '500', color: 'var(--color-gold)' }}>
          Criado por lucianosaints
        </p>
      </footer>
    </div>
  );
}
