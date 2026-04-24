import { resolveImageUrl } from "../utils/imageUrl";

export default function ProductCard({ product, quantity, onAdd, onDec }) {
  const imageSrc = resolveImageUrl(product.image_url, product.name);

  return (
    <article className="product-card">
      <img
        className="product-image"
        src={imageSrc}
        alt={product.name}
        loading="lazy"
        onError={(event) => {
          event.currentTarget.src = resolveImageUrl("", product.name);
        }}
      />
      <div className="product-thumb">{product.sku}</div>
      <h3>{product.name}</h3>
      <p className="meta-row">{product.category}</p>
      <p className="price">${Number(product.price).toFixed(2)}</p>

      {quantity > 0 ? (
        <div className="product-qty-controls">
          <button type="button" onClick={() => onDec(product.sku)}>
            -
          </button>
          <span>{quantity} in cart</span>
          <button type="button" onClick={() => onAdd(product.sku)}>
            +
          </button>
        </div>
      ) : (
        <button className="primary-btn" onClick={() => onAdd(product.sku)} type="button">
          Add to Cart
        </button>
      )}
    </article>
  );
}
