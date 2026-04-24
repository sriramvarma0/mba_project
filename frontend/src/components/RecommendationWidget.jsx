import { resolveImageUrl } from "../utils/imageUrl";

export default function RecommendationWidget({ recommendations, onAdd }) {
  if (!recommendations.length) {
    return (
      <section className="panel">
        <h3>Frequently Bought Together</h3>
        <p>No suggestions yet. Add more items to your cart.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h3>Frequently Bought Together</h3>
      <div className="recommend-grid">
        {recommendations.map((rec) => (
          <article key={rec.sku} className="recommend-card">
            <img
              className="recommend-image"
              src={resolveImageUrl(rec.product.image_url, rec.product.name)}
              alt={rec.product.name}
              loading="lazy"
              onError={(event) => {
                event.currentTarget.src = resolveImageUrl("", rec.product.name);
              }}
            />
            <h4>{rec.product.name}</h4>
            <p>{rec.sku}</p>
            <div className="badge-row">
              <span className="confidence">Confidence {(rec.confidence * 100).toFixed(1)}%</span>
              <span className="lift">Lift {rec.lift.toFixed(2)}</span>
            </div>
            <button className="primary-btn" type="button" onClick={() => onAdd(rec.sku)}>
              Add to Cart
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
