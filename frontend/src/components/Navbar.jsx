import { NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function Navbar({ cartCount, user }) {
  const { logout } = useAuth();

  const navClass = ({ isActive }) => (isActive ? "nav-pill active" : "nav-pill");

  return (
    <header className="navbar">
      <div className="brand-block">
        <h1>BasketPulse</h1>
        <p>FP-Growth recommendation engine</p>
      </div>
      <nav className="nav-links">
        <NavLink to="/" className={navClass}>
          Storefront
        </NavLink>
        <NavLink to="/cart" className={navClass}>
          Cart ({cartCount})
        </NavLink>
        {user?.role === "admin" && (
          <>
            <NavLink to="/admin/dashboard" className={navClass}>
              Dashboard
            </NavLink>
            <NavLink to="/admin/upload" className={navClass}>
              Upload
            </NavLink>
            <NavLink to="/admin/rules" className={navClass}>
              Rules
            </NavLink>
            <NavLink to="/admin/reports" className={navClass}>
              Reports
            </NavLink>
          </>
        )}
        {!user && (
          <NavLink to="/login" className={navClass}>
            Login
          </NavLink>
        )}
        {!user && (
          <NavLink to="/register" className={navClass}>
            Register
          </NavLink>
        )}
        {user && (
          <button className="ghost-btn nav-pill" onClick={logout} type="button">
            Logout
          </button>
        )}
      </nav>
    </header>
  );
}
