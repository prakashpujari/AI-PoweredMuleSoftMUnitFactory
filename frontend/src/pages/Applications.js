import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Box, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Select, MenuItem, FormControl, InputLabel, Alert, CircularProgress, Chip, LinearProgress, IconButton, Tooltip, } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { Add, Refresh, PlayArrow, Assessment } from "@mui/icons-material";
import { applicationsApi, munitApi, executionApi } from "../services/api";
import { MOCK_APPLICATIONS } from "../services/mockData";
const StatusChip = ({ status }) => {
    const colorMap = {
        tested: "success",
        analyzed: "info",
        discovered: "default",
        generating: "warning",
        failed: "error",
    };
    return _jsx(Chip, { label: status, size: "small", color: colorMap[status] ?? "default" });
};
const ScoreBar = ({ value }) => (_jsxs(Box, { display: "flex", alignItems: "center", gap: 1, width: "100%", children: [_jsx(LinearProgress, { variant: "determinate", value: Math.min(value, 100), sx: { flex: 1, height: 8, borderRadius: 4 }, color: value >= 90 ? "success" : value >= 70 ? "warning" : "error" }), _jsxs(Typography, { variant: "caption", minWidth: 35, children: [value.toFixed(0), "%"] })] }));
const Applications = () => {
    const [apps, setApps] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [scanDialogOpen, setScanDialogOpen] = useState(false);
    const [scanForm, setScanForm] = useState({
        repo_path: "",
        business_unit: "",
        domain: "",
        environment: "development",
        api_type: "unknown",
        ai_provider: "groq",
    });
    const [scanning, setScanning] = useState(false);
    const fetchApps = async () => {
        setLoading(true);
        try {
            const res = await applicationsApi.list({ limit: 200 });
            setApps(res.data);
        }
        catch (_e) {
            setApps(MOCK_APPLICATIONS); // fallback to demo data
        }
        finally {
            setLoading(false);
        }
    };
    useEffect(() => { fetchApps(); }, []);
    const handleScan = async () => {
        setScanning(true);
        try {
            await applicationsApi.scan(scanForm);
            setSuccess("Application scanned and inventoried successfully");
            setScanDialogOpen(false);
            fetchApps();
        }
        catch (e) {
            setError(e.response?.data?.message ?? "Scan failed");
        }
        finally {
            setScanning(false);
        }
    };
    const handleGenerateTests = async (appId) => {
        try {
            await munitApi.generate({ application_id: appId, ai_provider: "groq" });
            setSuccess("MUnit tests generated successfully");
            fetchApps();
        }
        catch (e) {
            setError(e.response?.data?.message ?? "Test generation failed");
        }
    };
    const handleExecute = async (appId) => {
        try {
            await executionApi.run({ application_id: appId });
            setSuccess("Test execution started");
            fetchApps();
        }
        catch (e) {
            setError(e.response?.data?.message ?? "Execution failed");
        }
    };
    const columns = [
        { field: "name", headerName: "Application", width: 200, renderCell: (p) => (_jsx(Typography, { variant: "body2", fontWeight: 600, children: p.value })) },
        { field: "mule_runtime_version", headerName: "Runtime", width: 100 },
        { field: "api_type", headerName: "API Type", width: 110, renderCell: (p) => (_jsx(Chip, { label: p.value?.toUpperCase(), size: "small", variant: "outlined" })) },
        { field: "status", headerName: "Status", width: 110, renderCell: (p) => (_jsx(StatusChip, { status: p.value })) },
        { field: "flows_count", headerName: "Flows", width: 80, type: "number" },
        { field: "coverage_score", headerName: "Coverage", width: 160, renderCell: (p) => (_jsx(ScoreBar, { value: p.value ?? 0 })) },
        { field: "production_readiness_score", headerName: "Readiness", width: 160, renderCell: (p) => (_jsx(ScoreBar, { value: p.value ?? 0 })) },
        { field: "business_unit", headerName: "Business Unit", width: 140 },
        { field: "environment", headerName: "Environment", width: 120 },
        {
            field: "actions",
            headerName: "Actions",
            width: 140,
            sortable: false,
            renderCell: (p) => (_jsxs(Box, { display: "flex", gap: 0.5, children: [_jsx(Tooltip, { title: "Generate MUnit Tests", children: _jsx(IconButton, { size: "small", color: "primary", onClick: () => handleGenerateTests(p.row.id), children: _jsx(Add, { fontSize: "small" }) }) }), _jsx(Tooltip, { title: "Execute Tests", children: _jsx(IconButton, { size: "small", color: "success", onClick: () => handleExecute(p.row.id), children: _jsx(PlayArrow, { fontSize: "small" }) }) }), _jsx(Tooltip, { title: "View Report", children: _jsx(IconButton, { size: "small", color: "secondary", children: _jsx(Assessment, { fontSize: "small" }) }) })] })),
        },
    ];
    return (_jsxs(Box, { sx: { p: 3 }, children: [_jsxs(Box, { display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3, children: [_jsx(Typography, { variant: "h5", fontWeight: 700, children: "Applications" }), _jsxs(Box, { display: "flex", gap: 2, children: [_jsx(Button, { startIcon: _jsx(Refresh, {}), onClick: fetchApps, variant: "outlined", children: "Refresh" }), _jsx(Button, { startIcon: _jsx(Add, {}), variant: "contained", onClick: () => setScanDialogOpen(true), children: "Scan Application" })] })] }), error && _jsx(Alert, { severity: "error", sx: { mb: 2 }, onClose: () => setError(null), children: error }), success && _jsx(Alert, { severity: "success", sx: { mb: 2 }, onClose: () => setSuccess(null), children: success }), _jsx(DataGrid, { rows: apps, columns: columns, loading: loading, initialState: { pagination: { paginationModel: { pageSize: 25 } } }, pageSizeOptions: [25, 50, 100], disableRowSelectionOnClick: true, sx: { height: 600, borderRadius: 3 } }), _jsxs(Dialog, { open: scanDialogOpen, onClose: () => setScanDialogOpen(false), maxWidth: "sm", fullWidth: true, children: [_jsx(DialogTitle, { children: "Scan MuleSoft Application" }), _jsx(DialogContent, { children: _jsxs(Box, { display: "flex", flexDirection: "column", gap: 2, mt: 1, children: [_jsx(TextField, { label: "Repository Path", value: scanForm.repo_path, onChange: e => setScanForm(f => ({ ...f, repo_path: e.target.value })), placeholder: "/path/to/mule-project", required: true, fullWidth: true }), _jsx(TextField, { label: "Business Unit", value: scanForm.business_unit, onChange: e => setScanForm(f => ({ ...f, business_unit: e.target.value })), fullWidth: true }), _jsx(TextField, { label: "Domain", value: scanForm.domain, onChange: e => setScanForm(f => ({ ...f, domain: e.target.value })), fullWidth: true }), _jsxs(FormControl, { fullWidth: true, children: [_jsx(InputLabel, { children: "API Type" }), _jsxs(Select, { value: scanForm.api_type, onChange: e => setScanForm(f => ({ ...f, api_type: e.target.value })), children: [_jsx(MenuItem, { value: "system", children: "System API" }), _jsx(MenuItem, { value: "process", children: "Process API" }), _jsx(MenuItem, { value: "experience", children: "Experience API" }), _jsx(MenuItem, { value: "unknown", children: "Unknown" })] })] }), _jsxs(FormControl, { fullWidth: true, children: [_jsx(InputLabel, { children: "AI Provider" }), _jsxs(Select, { value: scanForm.ai_provider, onChange: e => setScanForm(f => ({ ...f, ai_provider: e.target.value })), children: [_jsx(MenuItem, { value: "groq", children: "Groq (llama-3.3-70b)" }), _jsx(MenuItem, { value: "anthropic", children: "Claude (Anthropic)" }), _jsx(MenuItem, { value: "openai", children: "GPT-4o (OpenAI)" })] })] })] }) }), _jsxs(DialogActions, { children: [_jsx(Button, { onClick: () => setScanDialogOpen(false), children: "Cancel" }), _jsx(Button, { onClick: handleScan, variant: "contained", disabled: !scanForm.repo_path || scanning, children: scanning ? _jsx(CircularProgress, { size: 20 }) : "Scan" })] })] })] }));
};
export default Applications;
