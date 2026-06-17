/**
 * CardResult — Exibição do resultado da identificação
 *
 * Mostra a carta identificada com:
 * - Imagem HD do Scryfall
 * - Nome em inglês e português
 * - Tipo, custo de mana, raridade
 * - Texto do oráculo (EN e PT)
 * - Link para o Scryfall
 */
export default function CardResult({ card }) {
  if (!card) return null;

  const rarityClass = `card-result__rarity-badge card-result__rarity-badge--${card.rarity || 'common'}`;

  return (
    <div className="card-result">
      {/* Imagem HD da carta */}
      {card.image_url && (
        <div className="card-result__image-wrapper">
          <img
            className="card-result__image"
            src={card.image_url}
            alt={card.name_pt || card.name_en}
            loading="lazy"
          />
          {card.rarity && (
            <span className={rarityClass} id="rarity-badge">
              {card.rarity}
            </span>
          )}
        </div>
      )}

      {/* Informações da carta */}
      <div className="glass-card card-result__info">
        {/* Nome EN */}
        <h2 className="card-result__name-en" id="card-name-en">
          {card.name_en}
        </h2>

        {/* Nome PT */}
        {card.name_pt && (
          <p className="card-result__name-pt" id="card-name-pt">
            {card.name_pt}
          </p>
        )}

        {/* Meta: tipo, mana, edição */}
        <div className="card-result__meta">
          {card.type && (
            <span className="card-result__meta-tag" id="card-type">
              ⚔️ {card.type}
            </span>
          )}
          {card.mana_cost && (
            <span className="card-result__meta-tag" id="card-mana">
              💧 {card.mana_cost}
            </span>
          )}
          {card.set_name && (
            <span className="card-result__meta-tag" id="card-set">
              📦 {card.set_name}
            </span>
          )}
        </div>



        {/* Texto do Oráculo — Português */}
        {card.oracle_text_pt && (
          <div className="card-result__section">
            <h3 className="card-result__section-title">Texto Traduzido 🇧🇷</h3>
            <p className="card-result__oracle-text card-result__oracle-text--pt" id="oracle-text-pt">
              {card.oracle_text_pt}
            </p>
          </div>
        )}

        {/* Link para Scryfall */}
        {card.scryfall_url && (
          <a
            className="card-result__link"
            href={card.scryfall_url}
            target="_blank"
            rel="noopener noreferrer"
            id="scryfall-link"
          >
            🔗 Ver no Scryfall →
          </a>
        )}
      </div>
    </div>
  );
}
