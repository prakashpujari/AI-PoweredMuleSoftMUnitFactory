import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Box, Grid, Typography, Paper, Chip, Divider, Alert, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button, LinearProgress, } from "@mui/material";
import { Download, CheckCircle, Warning } from "@mui/icons-material";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { reportsApi } from "../services/api";
import { MOCK_EXECUTIVE_REPORT } from "../services/mockData";
const riskColors = {
    LOW: "#2e7d32",
    MEDIUM: "#f57c00",
    HIGH: "#d84315",
    CRITICAL: "#b71c1c",
};
const RecommendationBadge = ({ text }) => {
    const approved = text.includes("APPROVED");
    return (_jsxs(Box, { sx: {
            display: "inline-flex",
            alignItems: "center",
            gap: 1,
            px: 3,
            py: 1.5,
            borderRadius: 3,
            bgcolor: approved ? "#e8f5e9" : "#fff3e0",
            border: `2px solid ${approved ? "#2e7d32" : "#f57c00"}`,
            color: approved ? "#2e7d32" : "#e65100",
            fontWeight: 700,
            fontSize: "1.1rem",
        }, children: [approved ? _jsx(CheckCircle, {}) : _jsx(Warning, {}), text] }));
};
const ScoreGauge = ({ label, value, color = "#1a237e", }) => (_jsxs(Box, { textAlign: "center", children: [_jsxs(Box, { position: "relative", display: "inline-flex", mb: 1, children: [_jsx(CircularProgress, { variant: "determinate", value: value, size: 90, thickness: 6, sx: { color } }), _jsx(Box, { sx: {
                        position: "absolute", top: 0, left: 0, bottom: 0, right: 0,
                        display: "flex", alignItems: "center", justifyContent: "center",
                    }, children: _jsx(Typography, { variant: "h6", fontWeight: 700, color: color, children: Math.round(value) }) })] }), _jsx(Typography, { variant: "body2", color: "text.secondary", fontWeight: 500, children: label })] }));
const ExecutiveReport = () => {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        reportsApi.getExecutive()
            .then(res => setReport(res.data))
            .catch((_err) => {
            setError("Could not load live data — showing demo report");
            setReport(MOCK_EXECUTIVE_REPORT);
        })
            .finally(() => setLoading(false));
    }, []);
    if (loading)
        return (_jsx(Box, { display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh", children: _jsx(CircularProgress, { size: 60 }) }));
    if (!report)
        return null;
    const buChartData = report.business_unit_breakdown.map(b => ({
        name: b.business_unit || "Unknown",
        coverage: b.avg_coverage,
        count: b.count,
    }));
    return (_jsxs(Box, { sx: { p: 3 }, children: [error && (_jsx(Alert, { severity: "info", sx: { mb: 2 }, onClose: () => setError(null), children: error })), _jsxs(Box, { display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 3, children: [_jsxs(Box, { children: [_jsx(Typography, { variant: "h4", fontWeight: 700, color: "primary", children: "Executive Report" }), _jsxs(Typography, { color: "text.secondary", children: ["Generated: ", new Date(report.generated_at).toLocaleString()] })] }), _jsx(Button, { variant: "contained", startIcon: _jsx(Download, {}), size: "large", onClick: () => window.print(), children: "Download PDF" })] }), _jsx(Box, { mb: 3, display: "flex", justifyContent: "center", children: _jsx(RecommendationBadge, { text: report.recommendation }) }), _jsx(Grid, { container: true, spacing: 2, mb: 3, children: [
                    { label: "Applications Scanned", value: report.applications_scanned },
                    { label: "Applications Tested", value: report.applications_tested },
                    { label: "Tests Executed", value: report.tests_executed.toLocaleString() },
                    { label: "Tests Passed", value: report.tests_passed.toLocaleString() },
                    { label: "Tests Failed", value: report.tests_failed.toLocaleString() },
                    { label: "Pass Rate", value: `${report.pass_rate.toFixed(1)}%` },
                    { label: "Coverage", value: `${report.coverage_percent.toFixed(1)}%` },
                    { label: "Confidence Score", value: `${(report.confidence_score * 100).toFixed(0)}%` },
                ].map((item) => (_jsx(Grid, { item: true, xs: 6, sm: 3, children: _jsxs(Paper, { elevation: 1, sx: { p: 2, borderRadius: 2, textAlign: "center" }, children: [_jsx(Typography, { variant: "h5", fontWeight: 700, color: "primary", children: item.value }), _jsx(Typography, { variant: "caption", color: "text.secondary", children: item.label })] }) }, item.label))) }), _jsxs(Paper, { elevation: 2, sx: { p: 3, mb: 3, borderRadius: 3, display: "flex", alignItems: "center", gap: 3 }, children: [_jsxs(Box, { children: [_jsx(Typography, { variant: "overline", color: "text.secondary", children: "Risk Level" }), _jsx(Box, { children: _jsx(Chip, { label: report.risk_level, sx: {
                                        bgcolor: riskColors[report.risk_level] ?? "#1a237e",
                                        color: "white",
                                        fontWeight: 700,
                                        fontSize: "1rem",
                                        px: 2,
                                        height: 40,
                                    } }) })] }), _jsx(Divider, { orientation: "vertical", flexItem: true }), _jsxs(Box, { flex: 1, children: [_jsx(Typography, { variant: "overline", color: "text.secondary", children: "Migration Readiness" }), _jsxs(Box, { display: "flex", alignItems: "center", gap: 2, children: [_jsx(LinearProgress, { variant: "determinate", value: report.migration_readiness, sx: { flex: 1, height: 10, borderRadius: 5 }, color: report.migration_readiness >= 70 ? "success" : "warning" }), _jsxs(Typography, { variant: "h6", fontWeight: 700, children: [report.migration_readiness.toFixed(0), "%"] })] })] })] }), _jsxs(Paper, { elevation: 2, sx: { p: 3, mb: 3, borderRadius: 3 }, children: [_jsx(Typography, { variant: "h6", fontWeight: 600, mb: 3, children: "Quality Scorecards" }), _jsxs(Grid, { container: true, justifyContent: "space-around", children: [_jsx(Grid, { item: true, children: _jsx(ScoreGauge, { label: "Security", value: report.security_score, color: "#6a1b9a" }) }), _jsx(Grid, { item: true, children: _jsx(ScoreGauge, { label: "Performance", value: report.performance_score, color: "#00838f" }) }), _jsx(Grid, { item: true, children: _jsx(ScoreGauge, { label: "Production Readiness", value: report.production_readiness, color: "#1a237e" }) }), _jsx(Grid, { item: true, children: _jsx(ScoreGauge, { label: "Coverage", value: report.coverage_percent, color: "#2e7d32" }) }), _jsx(Grid, { item: true, children: _jsx(ScoreGauge, { label: "Pass Rate", value: report.pass_rate, color: "#f57c00" }) })] })] }), buChartData.length > 0 && (_jsxs(Paper, { elevation: 2, sx: { p: 3, mb: 3, borderRadius: 3 }, children: [_jsx(Typography, { variant: "h6", fontWeight: 600, mb: 2, children: "Coverage by Business Unit" }), _jsx(ResponsiveContainer, { width: "100%", height: 250, children: _jsxs(BarChart, { data: buChartData, layout: "vertical", children: [_jsx(CartesianGrid, { strokeDasharray: "3 3" }), _jsx(XAxis, { type: "number", domain: [0, 100], unit: "%" }), _jsx(YAxis, { dataKey: "name", type: "category", width: 120 }), _jsx(Tooltip, { formatter: (v) => `${v.toFixed(1)}%` }), _jsx(Bar, { dataKey: "coverage", radius: [0, 4, 4, 0], children: buChartData.map((entry, i) => (_jsx(Cell, { fill: entry.coverage >= 95 ? "#2e7d32" : entry.coverage >= 80 ? "#f57c00" : "#c62828" }, i))) })] }) })] })), _jsxs(Paper, { elevation: 2, sx: { p: 3, borderRadius: 3 }, children: [_jsx(Typography, { variant: "h6", fontWeight: 600, mb: 2, children: "Applications by API Classification" }), _jsx(TableContainer, { children: _jsxs(Table, { size: "small", children: [_jsx(TableHead, { children: _jsxs(TableRow, { sx: { bgcolor: "#f5f5f5" }, children: [_jsx(TableCell, { children: _jsx("strong", { children: "API Type" }) }), _jsx(TableCell, { align: "right", children: _jsx("strong", { children: "Count" }) }), _jsx(TableCell, { children: _jsx("strong", { children: "Classification" }) })] }) }), _jsx(TableBody, { children: report.api_type_breakdown.map((row) => (_jsxs(TableRow, { hover: true, children: [_jsx(TableCell, { sx: { textTransform: "capitalize" }, children: row.api_type }), _jsx(TableCell, { align: "right", children: row.count }), _jsx(TableCell, { children: _jsx(Chip, { label: row.api_type === "system" ? "System API (Layer 1)" :
                                                        row.api_type === "process" ? "Process API (Layer 2)" :
                                                            row.api_type === "experience" ? "Experience API (Layer 3)" : "Uncategorized", size: "small", color: row.api_type === "experience" ? "primary" :
                                                        row.api_type === "process" ? "secondary" : "default" }) })] }, row.api_type))) })] }) })] })] }));
};
export default ExecutiveReport;
