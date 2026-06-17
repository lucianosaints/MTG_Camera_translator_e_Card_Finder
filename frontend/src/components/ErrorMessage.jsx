/**
 * ErrorMessage — Componente de exibição de erros
 *
 * Mostra mensagens de erro amigáveis ao usuário.
 * Nunca exibe detalhes técnicos internos.
 */
export default function ErrorMessage({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="error-message" role="alert" id="error-message">
      <span className="error-message__icon">⚠️</span>
      <div>
        <p>{message}</p>
        {onDismiss && (
          <button
            className="btn btn--secondary"
            onClick={onDismiss}
            style={{ marginTop: '0.75rem', padding: '0.4rem 1rem', fontSize: '0.85rem' }}
            id="btn-dismiss-error"
          >
            Tentar novamente
          </button>
        )}
      </div>
    </div>
  );
}
