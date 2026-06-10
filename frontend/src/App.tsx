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
      <Box sx={{ p: 2 }}>
        <Chip
          label="v1.0.0"
          size="small"
          sx={{ bgcolor: "rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.8)" }}
        />
      </Box>
    </Drawer>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Box sx={{ display: "flex", minHeight: "100vh" }}>
          <Sidebar />
          <Box
            component="main"
            sx={{ flexGrow: 1, bgcolor: "background.default", overflow: "auto" }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/applications" element={<Applications />} />
              <Route path="/executive-report" element={<ExecutiveReport />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </Box>
        </Box>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
