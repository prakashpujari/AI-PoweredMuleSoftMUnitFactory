import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { Box, Button, TextField, Typography, Paper, Alert, CircularProgress, InputAdornment, IconButton, } from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { authApi } from "../services/api";
const Login = ({ onLogin }) => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPass, setShowPass] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const res = await authApi.login(email, password);
            onLogin(res.data.access_token);
        }
        catch (err) {
            const detail = err.response?.data?.detail ?? "Invalid email or password";
            setError(typeof detail === "string" ? detail : JSON.stringify(detail));
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsx(Box, { sx: {
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            bgcolor: "#f0f4ff",
            backgroundImage: "radial-gradient(circle at 20% 50%, #1a237e22 0%, transparent 50%), radial-gradient(circle at 80% 20%, #0288d122 0%, transparent 50%)",
        }, children: _jsxs(Paper, { elevation: 4, sx: { p: 5, width: "100%", maxWidth: 420, borderRadius: 3 }, children: [_jsxs(Box, { sx: { mb: 4, textAlign: "center" }, children: [_jsx(Typography, { variant: "h5", fontWeight: 800, color: "primary.main", children: "AI-MUnit-Factory" }), _jsx(Typography, { variant: "body2", color: "text.secondary", mt: 0.5, children: "Enterprise MuleSoft Testing Platform" })] }), _jsx(Typography, { variant: "h6", fontWeight: 700, mb: 3, children: "Sign in to your account" }), error && (_jsx(Alert, { severity: "error", sx: { mb: 2 }, children: error })), _jsxs(Box, { component: "form", onSubmit: handleSubmit, children: [_jsx(TextField, { label: "Email", type: "email", fullWidth: true, required: true, value: email, onChange: (e) => setEmail(e.target.value), autoComplete: "email", sx: { mb: 2 } }), _jsx(TextField, { label: "Password", type: showPass ? "text" : "password", fullWidth: true, required: true, value: password, onChange: (e) => setPassword(e.target.value), autoComplete: "current-password", sx: { mb: 3 }, InputProps: {
                                endAdornment: (_jsx(InputAdornment, { position: "end", children: _jsx(IconButton, { onClick: () => setShowPass((v) => !v), edge: "end", children: showPass ? _jsx(VisibilityOff, {}) : _jsx(Visibility, {}) }) })),
                            } }), _jsx(Button, { type: "submit", variant: "contained", fullWidth: true, size: "large", disabled: loading, sx: { py: 1.5, fontWeight: 700 }, children: loading ? _jsx(CircularProgress, { size: 22, color: "inherit" }) : "Sign In" })] })] }) }));
};
export default Login;
