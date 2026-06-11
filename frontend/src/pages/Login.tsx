import React, { useState } from "react";
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
} from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { authApi } from "../services/api";

interface LoginProps {
  onLogin: (token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.login(email, password);
      onLogin(res.data.access_token);
    } catch (err: any) {
      const detail = err.response?.data?.detail ?? "Invalid email or password";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "#f0f4ff",
        backgroundImage:
          "radial-gradient(circle at 20% 50%, #1a237e22 0%, transparent 50%), radial-gradient(circle at 80% 20%, #0288d122 0%, transparent 50%)",
      }}
    >
      <Paper
        elevation={4}
        sx={{ p: 5, width: "100%", maxWidth: 420, borderRadius: 3 }}
      >
        {/* Brand */}
        <Box sx={{ mb: 4, textAlign: "center" }}>
          <Typography variant="h5" fontWeight={800} color="primary.main">
            AI-MUnit-Factory
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={0.5}>
            Enterprise MuleSoft Testing Platform
          </Typography>
        </Box>

        <Typography variant="h6" fontWeight={700} mb={3}>
          Sign in to your account
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            label="Email"
            type="email"
            fullWidth
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            sx={{ mb: 2 }}
          />
          <TextField
            label="Password"
            type={showPass ? "text" : "password"}
            fullWidth
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            sx={{ mb: 3 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowPass((v) => !v)} edge="end">
                    {showPass ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            disabled={loading}
            sx={{ py: 1.5, fontWeight: 700 }}
          >
            {loading ? <CircularProgress size={22} color="inherit" /> : "Sign In"}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default Login;
