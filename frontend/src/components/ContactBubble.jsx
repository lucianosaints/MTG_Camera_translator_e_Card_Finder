import React, { useState } from 'react';

export default function ContactBubble() {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 1000, display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
      
      {/* Tooltip com o email (aparece quando passa o mouse) */}
      <div style={{
        opacity: showTooltip ? 1 : 0,
        visibility: showTooltip ? 'visible' : 'hidden',
        backgroundColor: '#1e1e2f',
        color: '#fff',
        padding: '8px 12px',
        borderRadius: '8px',
        marginBottom: '10px',
        fontSize: '0.9rem',
        border: '1px solid #d4af37',
        boxShadow: '0 4px 10px rgba(0,0,0,0.5)',
        transition: 'all 0.3s ease',
        transform: showTooltip ? 'translateY(0)' : 'translateY(10px)',
        pointerEvents: 'none',
        whiteSpace: 'nowrap'
      }}>
        lucianosaints@gmail.com
      </div>

      {/* Botão circular de e-mail */}
      <a
        href="mailto:lucianosaints@gmail.com"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        style={{
          backgroundColor: '#d4af37',
          color: '#1a1a1a',
          width: '55px',
          height: '55px',
          borderRadius: '50%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          fontSize: '1.5rem',
          textDecoration: 'none',
          boxShadow: '0 4px 15px rgba(212, 175, 55, 0.4)',
          transition: 'transform 0.2s ease, background-color 0.2s',
          cursor: 'pointer'
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.transform = 'scale(1.1)';
          e.currentTarget.style.backgroundColor = '#f1c40f';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.backgroundColor = '#d4af37';
        }}
        title="Enviar e-mail para Suporte"
      >
        ✉️
      </a>
    </div>
  );
}
