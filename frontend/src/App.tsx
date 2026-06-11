import React, { useState, useEffect } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Chip,
  Divider,
} from "@mui/material";
import {
  Dashboard as DashboardIcon,
  Apps,
  Assessment,
  ExitToApp,
} from "@mui/icons-material";

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
  { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
  { label: "Applications", path: "/applications", icon: <Apps /> },
  { label: "Executive Report", path: "/executive-report", icon: <Assessment /> },
];

// ── Sidebar ───────────────────────────────────────────────────────────────────

const Sidebar: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
  const location = useLocation();
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        "& .MuiDrawer-paper": {
          width: DRAWER_WIDTH,
          bgcolor: "#1a237e",
          color: "white",
          border: "none",
        },
      }}
    >
      <Box sx={{ p: 3, pb: 2 }}>
        <Typography variant="h6" fontWeight={800} color="white">
          AI-MUnit-Factory
        </Typography>
        <Typography variant="caption" sx={{ opacity: 0.7 }}>
          Enterprise Testing Platform
        </Typography>
      </Box>
      <Divider sx={{ borderColor: "rgba(255,255,255,0.15)" }} />

      <List sx={{ px: 1, pt: 1 }}>
        {NAV_ITEMS.map((item) => {
          const active = location.pathname === item.path;
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                component={Link}
                to={item.path}
                sx={{
                  borderRadius: 2,
                  bgcolor: active ? "rgba(255,255,255,0.15)" : "transparent",
                  "&:hover": { bgcolor: "rgba(255,255,255,0.1)" },
                }}
              >
                <ListItemIcon
                  sx={{ color: active ? "white" : "rgba(255,255,255,0.7)", minWidth: 40 }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: "0.875rem",
                    fontWeight: active ? 700 : 400,
                    color: active ? "white" : "rgba(255,255,255,0.8)",
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Box sx={{ flexGrow: 1 }} />

      <Box sx={{ px: 1, pb: 1 }}>
        <ListItem disablePadding>
          <ListItemButton
            onClick={onLogout}
            sx={{ borderRadius: 2, "&:hover": { bgcolor: "rgba(255,255,255,0.1)" } }}
          >
            <ListItemIcon sx={{ color: "rgba(255,255,255,0.7)", minWidth: 40 }}>
              <ExitToApp />
            </ListItemIcon>
            <ListItemText
              primary="Logout"
              primaryTypographyProps={{ fontSize: "0.875rem", color: "rgba(255,255,255,0.8)" }}
            />
          </ListItemButton>
        </ListItem>
      </Box>

      <Box sx={{ px: 2, pb: 2 }}>
        <Chip
          label="v1.0.0"
          size="small"
          sx={{ bgcolor: "rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.8)" }}
        />
      </Box>
    </Drawer>
  );
};

// ── Auth-aware shell ──────────────────────────────────────────────────────────

const AuthenticatedShell: React.FC<{
  authenticated: boolean;
  onLogout: () => void;
  children: React.ReactNode;
}> = ({ authenticated, onLogout, children }) => {
  const navigate = useNavigate();

  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar onLogout={onLogout} />
      <Box
        component="main"
        sx={{ flexGrow: 1, bgcolor: "background.default", overflow: "auto" }}
      >
        {children}
      </Box>
    </Box>
  );
};

// ── Root App ──────────────────────────────────────────────────────────────────

const App: React.FC = () => {
  const [authenticated, setAuthenticated] = useState(
    () => !!localStorage.getItem("access_token")
  );

  // Listen for 401 events dispatched by the axios interceptor
  useEffect(() => {
    const handleLogout = () => setAuthenticated(false);
    window.addEventListener("auth:logout", handleLogout);
    return () => window.removeEventListener("auth:logout", handleLogout);
  }, []);

  const handleLogin = (token: string) => {
    localStorage.setItem("access_token", token);
    setAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setAuthenticated(false);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route
            path="/login"
            element={
              authenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Login onLogin={handleLogin} />
              )
            }
          />

          {/* Protected */}
          <Route
            path="/"
            element={
              <AuthenticatedShell authenticated={authenticated} onLogout={handleLogout}>
                <Dashboard />
              </AuthenticatedShell>
            }
          />
          <Route
            path="/applications"
            element={
              <AuthenticatedShell authenticated={authenticated} onLogout={handleLogout}>
                <Applications />
              </AuthenticatedShell>
            }
          />
          <Route
            path="/executive-report"
            element={
              <AuthenticatedShell authenticated={authenticated} onLogout={handleLogout}>
                <ExecutiveReport />
              </AuthenticatedShell>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
