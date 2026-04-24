import { resolveImageUrl } from "../utils/imageUrl";

export default function CartItem({ item, product, onAdd, onDec, onRemove }) {
  const name = product?.name || item.sku;
  const price = Number(product?.price || 0);

  return (
    <div className="cart-item">
      <div className="cart-main">
        <img
          className="cart-image"
          src={resolveImageUrl(product?.image_url, name)}
          alt={name}
          loading="lazy"
          onError={(event) => {
            event.currentTarget.src = resolveImageUrl("", name);
          }}
        />
        <div>
        <h4>{name}</h4>
        <p>{item.sku}</p>
        </div>
      </div>
      <div className="cart-controls">
        <button type="button" onClick={() => onDec(item.sku)}>
          -
        </button>
        <span>{item.qty}</span>
        <button type="button" onClick={() => onAdd(item.sku)}>
          +
        </button>
      </div>
      <div className="cart-actions">
        <strong>${(price * item.qty).toFixed(2)}</strong>
        <button type="button" onClick={() => onRemove(item.sku)}>
          Remove
        </button>
      </div>
    </div>
  );
}
