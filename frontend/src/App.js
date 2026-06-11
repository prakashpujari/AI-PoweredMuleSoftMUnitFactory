import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation, } from "react-router-dom";
import { Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Typography, CssBaseline, ThemeProvider, createTheme, Chip, Divider, } from "@mui/material";
import { Dashboard as DashboardIcon, Apps, Assessment, ExitToApp, } from "@mui/icons-material";
import Dashboard from "./pages/Dashboard";
import Applications from "./pages/Applications";
import ExecutiveReport from "./pages/ExecutiveReport";
import Login from "./pages/Login";
const theme = createTheme({
    palette: {
        primary: { main: "#1a237e" },
        secondary: { main: "#0288d1" },
        background: { default: "#f8faff" },
    },
    typography: {
        fontFamily: '"Inter", "Roboto", "Helvetica", sans-serif',
    },
    components: {
        MuiButton: {
            styleOverrides: { root: { borderRadius: 8, textTransform: "none", fontWeight: 600 } },
        },
        MuiCard: { styleOverrides: { root: { borderRadius: 12 } } },
    },
});
const DRAWER_WIDTH = 240;
const NAV_ITEMS = [
    { label: "Dashboard", path: "/", icon: _jsx(DashboardIcon, {}) },
    { label: "Applications", path: "/applications", icon: _jsx(Apps, {}) },
    { label: "Executive Report", path: "/executive-report", icon: _jsx(Assessment, {}) },
];
// ── Sidebar ───────────────────────────────────────────────────────────────────
const Sidebar = ({ onLogout }) => {
    const location = useLocation();
    return (_jsxs(Drawer, { variant: "permanent", sx: {
            width: DRAWER_WIDTH,
            "& .MuiDrawer-paper": {
                width: DRAWER_WIDTH,
                bgcolor: "#1a237e",
                color: "white",
                border: "none",
            },
        }, children: [_jsxs(Box, { sx: { p: 3, pb: 2 }, children: [_jsx(Typography, { variant: "h6", fontWeight: 800, color: "white", children: "AI-MUnit-Factory" }), _jsx(Typography, { variant: "caption", sx: { opacity: 0.7 }, children: "Enterprise Testing Platform" })] }), _jsx(Divider, { sx: { borderColor: "rgba(255,255,255,0.15)" } }), _jsx(List, { sx: { px: 1, pt: 1 }, children: NAV_ITEMS.map((item) => {
                    const active = location.pathname === item.path;
                    return (_jsx(ListItem, { disablePadding: true, sx: { mb: 0.5 }, children: _jsxs(ListItemButton, { component: Link, to: item.path, sx: {
                                borderRadius: 2,
                                bgcolor: active ? "rgba(255,255,255,0.15)" : "transparent",
                                "&:hover": { bgcolor: "rgba(255,255,255,0.1)" },
                            }, children: [_jsx(ListItemIcon, { sx: { color: active ? "white" : "rgba(255,255,255,0.7)", minWidth: 40 }, children: item.icon }), _jsx(ListItemText, { primary: item.label, primaryTypographyProps: {
                                        fontSize: "0.875rem",
                                        fontWeight: active ? 700 : 400,
                                        color: active ? "white" : "rgba(255,255,255,0.8)",
                                    } })] }) }, item.path));
                }) }), _jsx(Box, { sx: { flexGrow: 1 } }), _jsx(Box, { sx: { px: 1, pb: 1 }, children: _jsx(ListItem, { disablePadding: true, children: _jsxs(ListItemButton, { onClick: onLogout, sx: { borderRadius: 2, "&:hover": { bgcolor: "rgba(255,255,255,0.1)" } }, children: [_jsx(ListItemIcon, { sx: { color: "rgba(255,255,255,0.7)", minWidth: 40 }, children: _jsx(ExitToApp, {}) }), _jsx(ListItemText, { primary: "Logout", primaryTypographyProps: { fontSize: "0.875rem", color: "rgba(255,255,255,0.8)" } })] }) }) }), _jsx(Box, { sx: { px: 2, pb: 2 }, children: _jsx(Chip, { label: "v1.0.0", size: "small", sx: { bgcolor: "rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.8)" } }) })] }));
};
// ── Auth-aware shell ──────────────────────────────────────────────────────────
const AuthenticatedShell = ({ authenticated, onLogout, children }) => {
    if (!authenticated) {
        return _jsx(Navigate, { to: "/login", replace: true });
    }
    return (_jsxs(Box, { sx: { display: "flex", minHeight: "100vh" }, children: [_jsx(Sidebar, { onLogout: onLogout }), _jsx(Box, { component: "main", sx: { flexGrow: 1, bgcolor: "background.default", overflow: "auto" }, children: children })] }));
};
// ── Root App ──────────────────────────────────────────────────────────────────
const App = () => {
    const [authenticated, setAuthenticated] = useState(() => !!localStorage.getItem("access_token"));
    // Listen for 401 events dispatched by the axios interceptor
    useEffect(() => {
        const handleLogout = () => setAuthenticated(false);
        window.addEventListener("auth:logout", handleLogout);
        return () => window.removeEventListener("auth:logout", handleLogout);
    }, []);
    const handleLogin = (token) => {
        localStorage.setItem("access_token", token);
        setAuthenticated(true);
    };
    const handleLogout = () => {
        localStorage.removeItem("access_token");
        setAuthenticated(false);
    };
    return (_jsxs(ThemeProvider, { theme: theme, children: [_jsx(CssBaseline, {}), _jsx(BrowserRouter, { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/login", element: authenticated ? (_jsx(Navigate, { to: "/", replace: true })) : (_jsx(Login, { onLogin: handleLogin })) }), _jsx(Route, { path: "/", element: _jsx(AuthenticatedShell, { authenticated: authenticated, onLogout: handleLogout, children: _jsx(Dashboard, {}) }) }), _jsx(Route, { path: "/applications", element: _jsx(AuthenticatedShell, { authenticated: authenticated, onLogout: handleLogout, children: _jsx(Applications, {}) }) }), _jsx(Route, { path: "/executive-report", element: _jsx(AuthenticatedShell, { authenticated: authenticated, onLogout: handleLogout, children: _jsx(ExecutiveReport, {}) }) }), _jsx(Route, { path: "*", element: _jsx(Navigate, { to: "/", replace: true }) })] }) })] }));
};
export default App;
