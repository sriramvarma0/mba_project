import { useEffect, useMemo, useState } from "react";

import api from "../api/axios";
import ProductCard from "../components/ProductCard";
import RecommendationWidget from "../components/RecommendationWidget";

export default function Storefront({ products, cart, addToCart, decreaseQty }) {
  const [recommendations, setRecommendations] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  const cartSkus = useMemo(() => cart.map((item) => item.sku), [cart]);
  const filteredProducts = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    if (!query) {
      return products;
    }

    return products.filter((product) => {
      const name = String(product.name || "").toLowerCase();
      const sku = String(product.sku || "").toLowerCase();
      const category = String(product.category || "").toLowerCase();
      return name.includes(query) || sku.includes(query) || category.includes(query);
    });
  }, [products, searchTerm]);

  useEffect(() => {
    const loadRecommendations = async () => {
      if (!cartSkus.length) {
        setRecommendations([]);
        return;
      }

      try {
        const { data } = await api.post("/api/recommend", { cart_items: cartSkus });
        setRecommendations(data.recommendations || []);
      } catch (error) {
        setRecommendations([]);
      }
    };

    loadRecommendations();
  }, [cartSkus]);

  return (
    <section>
      <div className="hero-strip">
        <h2>Discover Smarter Bundles</h2>
        <p>Every cart update triggers market-basket intelligence for relevant add-ons.</p>
        <div className="hero-metrics">
          <span>{products.length} products loaded</span>
          <span>{filteredProducts.length} products shown</span>
          <span>{cartSkus.length} items in active cart</span>
          <span>{recommendations.length} live suggestions</span>
        </div>
      </div>

      <div className="store-search panel">
        <label htmlFor="store-search-input">Search Items</label>
        <input
          id="store-search-input"
          type="text"
          placeholder="Search by product name, SKU, or category"
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
        />
      </div>

      <RecommendationWidget recommendations={recommendations} onAdd={addToCart} />

      <div className="product-grid">
        {filteredProducts.map((product) => {
          const cartItem = cart.find((item) => item.sku === product.sku);
          const quantity = cartItem?.qty || 0;

          return (
            <ProductCard
              key={product.sku}
              product={product}
              quantity={quantity}
              onAdd={addToCart}
              onDec={decreaseQty}
            />
          );
        })}
      </div>

      {!filteredProducts.length && <p className="status-line">No matching items found. Try a different search.</p>}
    </section>
  );
}
