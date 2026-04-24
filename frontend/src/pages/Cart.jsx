import { useEffect, useMemo, useState } from "react";

import api from "../api/axios";
import CartItem from "../components/CartItem";
import RecommendationWidget from "../components/RecommendationWidget";

export default function Cart({ cart, products, addToCart, decreaseQty, removeFromCart }) {
  const [recommendations, setRecommendations] = useState([]);
  const [promoCode, setPromoCode] = useState(null);

  const cartSkus = useMemo(() => cart.map((item) => item.sku), [cart]);

  useEffect(() => {
    const fetchSignals = async () => {
      if (!cartSkus.length) {
        setRecommendations([]);
        setPromoCode(null);
        return;
      }

      try {
        const [recoRes, promoRes] = await Promise.all([
          api.post("/api/recommend", { cart_items: cartSkus }),
          api.post("/api/discount", { cart_items: cartSkus }),
        ]);
        setRecommendations(recoRes.data.recommendations || []);
        setPromoCode(promoRes.data.promo_code || null);
      } catch (error) {
        setRecommendations([]);
        setPromoCode(null);
      }
    };

    fetchSignals();
  }, [cartSkus]);

  const total = useMemo(
    () =>
      cart.reduce((sum, item) => {
        const product = products[item.sku];
        return sum + Number(product?.price || 0) * item.qty;
      }, 0),
    [cart, products]
  );

  return (
    <section>
      <h2 className="section-title">Cart</h2>
      {!cart.length && <p className="panel">Your cart is empty. Add items from storefront to unlock bundle suggestions.</p>}

      <div className="cart-list">
        {cart.map((item) => (
          <CartItem
            key={item.sku}
            item={item}
            product={products[item.sku]}
            onAdd={addToCart}
            onDec={decreaseQty}
            onRemove={removeFromCart}
          />
        ))}
      </div>

      <div className="total-row panel">
        <strong>Total: ${total.toFixed(2)}</strong>
        <span>{cart.length} unique items</span>
      </div>

      {promoCode && recommendations[0] && (
        <div className="promo-banner">
          Add {recommendations[0].product.name} now and get 10% off the bundle! ({promoCode})
        </div>
      )}

      <RecommendationWidget recommendations={recommendations} onAdd={addToCart} />
    </section>
  );
}
