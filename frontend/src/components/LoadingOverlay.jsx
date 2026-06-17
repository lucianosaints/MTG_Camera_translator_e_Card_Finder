/**
 * LoadingOverlay — Feedback visual durante processamento
 *
 * Exibe uma animação com orbe brilhante e mensagens
 * rotativas indicando o progresso da identificação.
 */
import { useState, useEffect } from 'react';

const LOADING_MESSAGES = [
  'Analisando a imagem...',
  'Consultando a IA de visão...',
  'Identificando a carta...',
  'Buscando dados no Scryfall...',
  'Traduzindo para português...',
  'Quase lá...',
];

export default function LoadingOverlay() {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-overlay" id="loading-overlay">
      <div className="loading-overlay__orb" />
      <p className="loading-overlay__text">
        {LOADING_MESSAGES[messageIndex]}
      </p>
      <p className="loading-overlay__step">
        Isso pode levar alguns segundos
      </p>
    </div>
  );
}
