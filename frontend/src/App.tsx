import React, { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import {
  Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText,
  AppBar, Toolbar, Typography, CssBaseline, ThemeProvider, createTheme,
  Avatar, Chip, Divider,
} from "@mui/material";
import {
  Dashboard as DashboardIcon, Apps, Assessment, BugReport,
  Storage, Security, Speed, ExitToApp,
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
    MuiButton: { styleOverrides: { root: { borderRadius: 8, textTransform: "none", fontWeight: 600 } } },
    MuiCard: { styleOverrides: { root: { borderRadius: 12 } } },
  },
});

const DRAWER_WIDTH = 240;

const NAV_ITEMS = [
  { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
  { label: "Applications", path: "/applications", icon: <Apps /> },
  { label: "Executive Report", path: "/executive-report", icon: <Assessment /> },
];

const Sidebar: React.FC = () => {
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  };

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
      {/* Logo */}
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
                <ListItemIcon sx={{ color: active ? "white" : "rgba(255,255,255,0.7)", minWidth: 40 }}>
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

      {/* Logout */}
      <Box sx={{ px: 1, pb: 1 }}>
        <ListItem disablePadding>
          <ListItemButton
            onClick={handleLogout}
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

const isAuthenticated = () => !!localStorage.getItem("access_token");

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Box sx={{ display: "flex", minHeight: "100vh" }}>
    <Sidebar />
    <Box component="main" sx={{ flexGrow: 1, bgcolor: "background.default", overflow: "auto" }}>
      {children}
    </Box>
  </Box>
);

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          {/* Public route — no sidebar */}
          <Route path="/login" element={<Login />} />

          {/* Protected routes — with sidebar */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Dashboard />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/applications"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Applications />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/executive-report"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ExecutiveReport />
                </AppLayout>
              </ProtectedRoute>
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
