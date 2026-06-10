import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Box, Grid, Typography, Alert, CircularProgress, Chip, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Divider, } from "@mui/material";
import { CheckCircle, Error, Speed, Security, Assessment, TrendingUp, CloudQueue, Warning, } from "@mui/icons-material";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer, } from "recharts";
import KPICard from "../components/dashboard/KPICard";
import { dashboardApi } from "../services/api";
import { MOCK_DASHBOARD } from "../services/mockData";
const COLORS = ["#1a237e", "#0288d1", "#2e7d32", "#f57c00", "#c62828", "#6a1b9a"];
const getRiskColor = (level) => {
    switch (level?.toUpperCase()) {
        case "CRITICAL": return "error";
        case "HIGH": return "error";
        case "MEDIUM": return "warning";
        case "LOW": return "success";
        default: return "default";
    }
};
const Dashboard = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                const res = await dashboardApi.get();
                setData(res.data);
            }
            catch (_err) {
                // Fallback to demo data when API is unavailable
                setData(MOCK_DASHBOARD);
            }
            finally {
                setLoading(false);
            }
        };
        fetchDashboard();
        const interval = setInterval(fetchDashboard, 60000);
        return () => clearInterval(interval);
    }, []);
    if (loading)
        return (_jsx(Box, { display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh", children: _jsx(CircularProgress, { size: 60 }) }));
    if (error)
        return _jsx(Alert, { severity: "error", sx: { m: 3 }, children: error });
    if (!data)
        return null;
    const severityChartData = Object.entries(data.failures?.by_severity ?? {}).map(([k, v]) => ({
        severity: k.toUpperCase(),
        count: v,
    }));
    const apiTypeData = Object.entries(data.breakdown?.by_api_type ?? {}).map(([k, v]) => ({
        name: k.toUpperCase(),
        value: v,
    }));
    return (_jsxs(Box, { sx: { p: 3 }, children: [_jsxs(Box, { display: "flex", alignItems: "center", justifyContent: "space-between", mb: 3, children: [_jsxs(Box, { children: [_jsx(Typography, { variant: "h4", fontWeight: 700, color: "primary", children: "AI-MUnit-Factory" }), _jsx(Typography, { variant: "subtitle1", color: "text.secondary", children: "Enterprise MuleSoft Testing Platform \u2014 Executive Dashboard" })] }), _jsx(Chip, { label: `Last updated: ${new Date(data.generated_at).toLocaleTimeString()}`, size: "small", color: "primary", variant: "outlined" })] }), _jsx(Divider, { sx: { mb: 3 } }), _jsxs(Grid, { container: true, spacing: 3, mb: 3, children: [_jsx(Grid, { item: true, xs: 12, sm: 6, md: 3, children: _jsx(KPICard, { title: "Applications Scanned", value: data.applications.total_scanned, subtitle: `${data.applications.total_tested} tested`, icon: _jsx(CloudQueue, {}), color: "#1a237e" }) }), _jsx(Grid, { item: true, xs: 12, sm: 6, md: 3, children: _jsx(KPICard, { title: "Tests Executed", value: data.tests.total_executed.toLocaleString(), subtitle: `${data.tests.passed.toLocaleString()} passed`, icon: _jsx(CheckCircle, {}), color: "#2e7d32", progress: data.tests.pass_rate, progressColor: "success" }) }), _jsx(Grid, { item: true, xs: 12, sm: 6, md: 3, children: _jsx(KPICard, { title: "Tests Failed", value: data.tests.failed.toLocaleString(), subtitle: `Pass rate: ${data.tests.pass_rate.toFixed(1)}%`, icon: _jsx(Error, {}), color: data.tests.failed > 0 ? "#c62828" : "#2e7d32" }) }), _jsx(Grid, { item: true, xs: 12, sm: 6, md: 3, children: _jsx(KPICard, { title: "Coverage %", value: `${data.coverage.average_overall.toFixed(1)}%`, subtitle: `Target: ${data.coverage.target}%`, icon: _jsx(Assessment, {}), color: "#f57c00", progress: data.coverage.average_overall, progressColor: data.coverage.average_overall >= 95 ? "success" : "warning" }) })] }), _jsxs(Grid, { container: true, spacing: 3, mb: 3, children: [_jsx(Grid, { item: true, xs: 12, sm: 6, md: 3, children: _jsx(KPICard, { title: "Production Readiness", value: `${data.scores.production_readiness.toFixed(0)}/100`, icon: _jsx(TrendingUp, {}), color: "#1565c0", progress: data.scores.production_readiness, progressColor: "primary", tooltip: "Weighted score based on test pass rate, coverage, and security" }) }), _jsx(Grid, { item: true, xs: 12, sm: 6, md: 3, children: _jsx(KPICard, { title: "Security Score", value: `${data.scores.security.toFixed(0)}/100`, icon: _jsx(Security, {}), color: "#6a1b9a", progress: data.scores.security, progressColor: "secondary" }) }), _jsx(Grid, { item: true, xs: 12, sm: 6, md: 3, children: _jsx(KPICard, { title: "Performance Score", value: `${data.scores.performance.toFixed(0)}/100`, icon: _jsx(Speed, {}), color: "#00838f", progress: data.scores.performance, progressColor: "info" }) }), _jsx(Grid, { item: true, xs: 12, sm: 6, md: 3, children: _jsx(KPICard, { title: "Risk Score", value: `${data.scores.risk.toFixed(0)}/100`, subtitle: "Lower is better", icon: _jsx(Warning, {}), color: data.scores.risk > 50 ? "#c62828" : data.scores.risk > 25 ? "#f57c00" : "#2e7d32", progress: data.scores.risk, progressColor: data.scores.risk > 50 ? "error" : data.scores.risk > 25 ? "warning" : "success", tooltip: "Risk score (0=no risk, 100=critical risk)" }) })] }), _jsxs(Grid, { container: true, spacing: 3, mb: 3, children: [_jsx(Grid, { item: true, xs: 12, md: 6, children: _jsxs(Paper, { elevation: 2, sx: { p: 3, borderRadius: 3 }, children: [_jsx(Typography, { variant: "h6", fontWeight: 600, mb: 2, children: "Failure Severity Distribution" }), _jsx(ResponsiveContainer, { width: "100%", height: 250, children: _jsxs(BarChart, { data: severityChartData, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3" }), _jsx(XAxis, { dataKey: "severity" }), _jsx(YAxis, {}), _jsx(Tooltip, {}), _jsx(Bar, { dataKey: "count", fill: "#1a237e", radius: [4, 4, 0, 0] })] }) })] }) }), _jsx(Grid, { item: true, xs: 12, md: 6, children: _jsxs(Paper, { elevation: 2, sx: { p: 3, borderRadius: 3 }, children: [_jsx(Typography, { variant: "h6", fontWeight: 600, mb: 2, children: "Applications by API Type" }), _jsx(ResponsiveContainer, { width: "100%", height: 250, children: _jsxs(PieChart, { children: [_jsx(Pie, { data: apiTypeData, dataKey: "value", nameKey: "name", cx: "50%", cy: "50%", outerRadius: 100, label: ({ name, value }) => `${name}: ${value}`, children: apiTypeData.map((_, index) => (_jsx(Cell, { fill: COLORS[index % COLORS.length] }, index))) }), _jsx(Tooltip, {}), _jsx(Legend, {})] }) })] }) })] }), _jsxs(Paper, { elevation: 2, sx: { borderRadius: 3 }, children: [_jsx(Box, { p: 3, pb: 1, children: _jsx(Typography, { variant: "h6", fontWeight: 600, children: "Recent Test Runs" }) }), _jsx(TableContainer, { children: _jsxs(Table, { size: "small", children: [_jsx(TableHead, { children: _jsxs(TableRow, { sx: { bgcolor: "#f5f5f5" }, children: [_jsx(TableCell, { children: _jsx("strong", { children: "Run #" }) }), _jsx(TableCell, { children: _jsx("strong", { children: "Status" }) }), _jsx(TableCell, { align: "right", children: _jsx("strong", { children: "Total" }) }), _jsx(TableCell, { align: "right", children: _jsx("strong", { children: "Passed" }) }), _jsx(TableCell, { align: "right", children: _jsx("strong", { children: "Failed" }) }), _jsx(TableCell, { align: "right", children: _jsx("strong", { children: "Pass Rate" }) }), _jsx(TableCell, { children: _jsx("strong", { children: "Date" }) })] }) }), _jsxs(TableBody, { children: [(data.recent_runs ?? []).map((run) => (_jsxs(TableRow, { hover: true, children: [_jsxs(TableCell, { children: ["#", run.run_number] }), _jsx(TableCell, { children: _jsx(Chip, { label: run.status, size: "small", color: run.status === "completed" ? "success" : run.status === "failed" ? "error" : "warning" }) }), _jsx(TableCell, { align: "right", children: run.total }), _jsx(TableCell, { align: "right", sx: { color: "success.main" }, children: run.passed }), _jsx(TableCell, { align: "right", sx: { color: run.failed > 0 ? "error.main" : "inherit" }, children: run.failed }), _jsx(TableCell, { align: "right", children: _jsx(Chip, { label: `${run.pass_rate.toFixed(1)}%`, size: "small", color: run.pass_rate >= 95 ? "success" : run.pass_rate >= 80 ? "warning" : "error", variant: "outlined" }) }), _jsx(TableCell, { children: new Date(run.created_at).toLocaleDateString() })] }, run.id))), (data.recent_runs ?? []).length === 0 && (_jsx(TableRow, { children: _jsx(TableCell, { colSpan: 7, align: "center", sx: { py: 3, color: "text.secondary" }, children: "No test runs yet. Start by scanning an application." }) }))] })] }) })] })] }));
};
export default Dashboard;
