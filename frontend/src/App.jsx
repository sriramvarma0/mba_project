import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";

import api from "./api/axios";
import Navbar from "./components/Navbar";
import Cart from "./pages/Cart";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Storefront from "./pages/Storefront";
import Dashboard from "./pages/admin/Dashboard";
import Reports from "./pages/admin/Reports";
import RulesManager from "./pages/admin/RulesManager";
import UploadData from "./pages/admin/UploadData";
import { useAuth } from "./context/AuthContext";

function AdminRoute({ children }) {
  const { isAdmin, authReady } = useAuth();
  if (!authReady) {
    return <p>Loading session...</p>;
  }
  if (!isAdmin) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function upsertCart(cart, sku, delta = 1) {
  const next = [...cart];
  const index = next.findIndex((item) => item.sku === sku);
  if (index === -1 && delta > 0) {
    next.push({ sku, qty: delta });
  } else if (index >= 0) {
    const qty = next[index].qty + delta;
    if (qty <= 0) {
      next.splice(index, 1);
    } else {
      next[index] = { ...next[index], qty };
    }
  }
  return next;
}

export default function App() {
  const { user } = useAuth();
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState(() => {
    const raw = localStorage.getItem("mba_cart");
    return raw ? JSON.parse(raw) : [];
  });

  useEffect(() => {
    localStorage.setItem("mba_cart", JSON.stringify(cart));
  }, [cart]);

  useEffect(() => {
    const loadProducts = async () => {
      try {
        const { data } = await api.get("/api/products");
        setProducts(data);
      } catch (error) {
        setProducts([]);
      }
    };
    loadProducts();
  }, []);

  const cartCount = useMemo(() => cart.reduce((acc, item) => acc + item.qty, 0), [cart]);

  const addToCart = (sku) => setCart((prev) => upsertCart(prev, sku, 1));
  const decreaseQty = (sku) => setCart((prev) => upsertCart(prev, sku, -1));
  const removeFromCart = (sku) => setCart((prev) => prev.filter((item) => item.sku !== sku));

  const productMap = useMemo(() => {
    const map = {};
    products.forEach((product) => {
      map[product.sku] = product;
    });
    return map;
  }, [products]);

  return (
    <div className="app-shell">
      <Navbar cartCount={cartCount} user={user} />
      <main className="page-shell">
        <Routes>
          <Route
            path="/"
            element={
              <Storefront
                products={products}
                cart={cart}
                addToCart={addToCart}
                decreaseQty={decreaseQty}
              />
            }
          />
          <Route
            path="/cart"
            element={
              <Cart
                cart={cart}
                products={productMap}
                addToCart={addToCart}
                decreaseQty={decreaseQty}
                removeFromCart={removeFromCart}
              />
            }
          />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/admin/dashboard"
            element={
              <AdminRoute>
                <Dashboard />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/upload"
            element={
              <AdminRoute>
                <UploadData />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/rules"
            element={
              <AdminRoute>
                <RulesManager />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/reports"
            element={
              <AdminRoute>
                <Reports />
              </AdminRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}
