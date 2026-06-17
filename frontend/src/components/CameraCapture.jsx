/**
 * CameraCapture — Componente de captura de imagem
 *
 * Permite ao usuário:
 * 1. Tirar foto com a câmera (mobile)
 * 2. Fazer upload de arquivo (desktop)
 * 3. Arrastar e soltar imagem (drag & drop)
 *
 * Validações no cliente:
 * - Apenas JPEG e PNG
 * - Máximo 5MB
 */
import { useState, useRef, useCallback, useEffect } from 'react';

const ALLOWED_TYPES = ['image/jpeg', 'image/png'];
const MAX_SIZE_MB = 5;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export default function CameraCapture({ onCapture, disabled }) {
  const [preview, setPreview] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  /**
   * Encerra a stream da câmera ativa
   */
  const stopWebcam = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsWebcamActive(false);
  }, []);

  // Garante que a câmera seja desligada se o componente for desmontado
  useEffect(() => {
    return () => stopWebcam();
  }, [stopWebcam]);

  /**
   * Inicia a captura da webcam (Ideal para Desktop/PC)
   */
  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      streamRef.current = stream;
      setIsWebcamActive(true);
      // Pequeno delay para o React renderizar a tag <video>
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }
      }, 100);
    } catch (err) {
      console.warn("Navegador não suporta acesso direto à câmera ou permissão negada.", err);
      // Fallback para o input nativo mobile caso o PC/Celular bloqueie a câmera
      cameraInputRef.current?.click();
    }
  };

  /**
   * Tira a foto a partir do vídeo ao vivo
   */
  const takeWebcamPhoto = () => {
    if (!videoRef.current) return;
    
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], "camera-capture.jpg", { type: "image/jpeg" });
      stopWebcam();
      handleFile(file);
    }, 'image/jpeg', 0.9);
  };

  /**
   * Valida e processa o arquivo selecionado.
   */
  const handleFile = useCallback(
    (file) => {
      if (!file) return;

      // Validar tipo (aceitamos jpeg, png, etc)
      if (!file.type.startsWith('image/')) {
        alert('Formato inválido. Envie uma imagem válida.');
        return;
      }

      // Validar tamanho
      if (file.size > MAX_SIZE_BYTES) {
        alert(`Arquivo muito grande. Máximo: ${MAX_SIZE_MB}MB.`);
        return;
      }

      // Criar preview
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);

      // Notificar componente pai
      onCapture(file);
    },
    [onCapture]
  );

  const handleFileInput = (e) => {
    handleFile(e.target.files?.[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };

  const removePreview = () => {
    setPreview(null);
    onCapture(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  return (
    <div className="camera-capture">
      {/* Inputs ocultos */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png"
        onChange={handleFileInput}
        style={{ display: 'none' }}
        id="file-upload"
        disabled={disabled}
      />
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileInput}
        style={{ display: 'none' }}
        id="camera-capture"
        disabled={disabled}
      />

      {isWebcamActive ? (
        /* Modo Câmera ao Vivo (WebRTC) */
        <div className="camera-capture__preview" style={{ background: '#000', borderRadius: '12px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <video 
            ref={videoRef} 
            autoPlay 
            playsInline 
            style={{ width: '100%', maxHeight: '300px', objectFit: 'cover' }}
          />
          <div style={{ display: 'flex', gap: '10px', padding: '10px', background: 'rgba(0,0,0,0.8)' }}>
            <button className="btn btn--primary" onClick={takeWebcamPhoto} style={{ flex: 2, padding: '10px' }}>
              📸 Tirar Foto
            </button>
            <button className="btn btn--secondary" onClick={stopWebcam} style={{ flex: 1, padding: '10px' }}>
              Cancelar
            </button>
          </div>
        </div>
      ) : preview ? (
        /* Preview da imagem selecionada */
        <div className="camera-capture__preview">
          <img src={preview} alt="Preview da carta" />
          {!disabled && (
            <div className="camera-capture__preview-overlay">
              <button
                className="camera-capture__remove-btn"
                onClick={removePreview}
                title="Remover imagem"
                id="btn-remove-preview"
              >
                ✕
              </button>
            </div>
          )}
        </div>
      ) : (
        /* Dropzone */
        <div
          className={`camera-capture__dropzone ${
            dragActive ? 'camera-capture__dropzone--active' : ''
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          id="dropzone"
        >
          <div className="camera-capture__dropzone-icon">📸</div>
          <p className="camera-capture__dropzone-text">
            Arraste uma foto de carta aqui
            <br />
            ou clique para selecionar
          </p>
          <p className="camera-capture__dropzone-hint">
            JPEG ou PNG • Máx. {MAX_SIZE_MB}MB
          </p>
        </div>
      )}

      {/* Botões de ação */}
      {!preview && !isWebcamActive && !disabled && (
        <div style={{ display: 'flex', gap: '0.75rem', width: '100%' }}>
          <button
            className="btn btn--secondary"
            onClick={() => fileInputRef.current?.click()}
            style={{ flex: 1 }}
            id="btn-upload-file"
          >
            📁 Arquivo
          </button>
          <button
            className="btn btn--secondary"
            onClick={startWebcam}
            style={{ flex: 1 }}
            id="btn-open-camera"
          >
            📷 Câmera
          </button>
        </div>
      )}
    </div>
  );
}
