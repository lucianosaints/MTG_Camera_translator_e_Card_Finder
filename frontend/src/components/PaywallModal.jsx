import React, { useState } from 'react';
import pixImg from '../imagem/pix.png';

export default function PaywallModal({ isOpen, onClose }) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const pixCode = "00020126330014br.gov.bcb.pix01110533267170952040000530398654049.995802BR5923LUCIANO SANTOS DA SILVA6007NITEROI62490511TradutorMTG50300017br.gov.bcb.brcode01051.0.06304B12E";

  const handleCopyPix = () => {
    navigator.clipboard.writeText(pixCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000); // Volta ao texto original após 3s
  };

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999
      }}
    >
      <div 
        style={{
          backgroundColor: '#1e1e2f',
          border: '1px solid #d4af37',
          borderRadius: '16px',
          padding: '2.5rem 2rem',
          maxWidth: '400px',
          width: '90%',
          textAlign: 'center',
          boxShadow: '0 0 30px rgba(212, 175, 55, 0.2)',
          color: '#fff',
          animation: 'fadeIn 0.3s ease-out',
          maxHeight: '90vh',
          overflowY: 'auto'
        }}
      >
        <div style={{ fontSize: '3.5rem', marginBottom: '0.5rem', filter: 'drop-shadow(0 0 10px rgba(212, 175, 55, 0.5))' }}>
          🔮
        </div>
        
        <h2 style={{ 
          color: '#d4af37', 
          marginBottom: '0.5rem', 
          fontWeight: '700',
          fontSize: '1.5rem',
          fontFamily: 'serif' 
        }}>
          Limite Diário Atingido
        </h2>
        
        <p style={{ 
          color: '#b0b0c0', 
          lineHeight: '1.5', 
          marginBottom: '1.5rem',
          fontSize: '0.95rem'
        }}>
          Você já identificou as suas 10 cartas diárias. 
          Desbloqueie o acesso Premium por <strong style={{ color: '#d4af37' }}>R$ 9,99</strong> e faça traduções ilimitadas!
        </p>

        {/* Bloco do PIX */}
        <div style={{ 
          backgroundColor: 'rgba(0,0,0,0.4)', 
          padding: '1rem', 
          borderRadius: '12px',
          marginBottom: '1.5rem',
          border: '1px solid rgba(255, 255, 255, 0.05)'
        }}>
          <img 
            src={pixImg} 
            alt="QR Code Pix" 
            style={{ 
              width: '180px', 
              height: '180px', 
              objectFit: 'contain', 
              borderRadius: '8px',
              backgroundColor: '#fff',
              padding: '8px',
              marginBottom: '1rem'
            }} 
          />
          
          <button 
            className="btn btn--primary btn--full"
            onClick={handleCopyPix}
            style={{ 
              backgroundColor: copied ? '#4caf50' : '#d4af37', 
              color: copied ? '#fff' : '#1a1a1a', 
              border: 'none',
              fontWeight: 'bold',
              padding: '12px',
              borderRadius: '8px',
              fontSize: '1rem',
              cursor: 'pointer',
              transition: 'all 0.3s',
              boxShadow: copied ? '0 0 10px rgba(76, 175, 80, 0.5)' : '0 4px 15px rgba(212, 175, 55, 0.4)'
            }}
          >
            {copied ? '✅ Código Pix Copiado!' : '📄 Copiar Pix (Copia e Cola)'}
          </button>
        </div>

        <button 
          onClick={onClose}
          style={{ 
            background: 'none', 
            border: 'none', 
            color: '#888', 
            fontSize: '0.9rem',
            textDecoration: 'underline',
            cursor: 'pointer',
            padding: '8px'
          }}
        >
          Talvez mais tarde
        </button>
      </div>
    </div>
  );
}
