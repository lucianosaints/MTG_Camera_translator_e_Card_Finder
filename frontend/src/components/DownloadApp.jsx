import React from 'react';
import './DownloadApp.css'; // Opcional, para estilizar

const DownloadApp = () => {
  return (
    <div className="download-app-container">
      <div className="download-card">
        <h3>Leve o MTG Translator com você!</h3>
        <p>Baixe nosso aplicativo Android oficial e tenha acesso mais rápido e direto no seu celular.</p>
        <a href="/download/app.apk" className="download-btn" download>
          Baixar App (APK)
        </a>
      </div>
    </div>
  );
};

export default DownloadApp;
