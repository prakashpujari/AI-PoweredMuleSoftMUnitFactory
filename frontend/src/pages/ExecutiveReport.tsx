import React, { useEffect, useState } from "react";
import {
  Box, Grid, Typography, Paper, Chip, Divider, Alert,
  CircularProgress, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Button, LinearProgress,
} from "@mui/material";
import { Download, CheckCircle, Cancel, Warning } from "@mui/icons-material";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { reportsApi } from "../services/api";
import { MOCK_EXECUTIVE_REPORT } from "../services/mockData";
import type { ExecutiveReport as ExecutiveReportType } from "../types";

const riskColors: Record<string, string> = {
  LOW: "#2e7d32",
  MEDIUM: "#f57c00",
  HIGH: "#d84315",
  CRITICAL: "#b71c1c",
};

const RecommendationBadge: React.FC<{ text: string }> = ({ text }) => {
  const approved = text.includes("APPROVED");
  return (
    <Box
      sx={{
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
      }}
    >
      {approved ? <CheckCircle /> : <Warning />}
      {text}
    </Box>
  );
};

const ScoreGauge: React.FC<{ label: string; value: number; color?: string }> = ({
  label, value, color = "#1a237e",
}) => (
  <Box textAlign="center">
    <Box position="relative" display="inline-flex" mb={1}>
      <CircularProgress
        variant="determinate"
        value={value}
        size={90}
        thickness={6}
        sx={{ color }}
      />
      <Box
        sx={{
          position: "absolute", top: 0, left: 0, bottom: 0, right: 0,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}
      >
        <Typography variant="h6" fontWeight={700} color={color}>
          {Math.round(value)}
        </Typography>
      </Box>
    </Box>
    <Typography variant="body2" color="text.secondary" fontWeight={500}>
      {label}
    </Typography>
  </Box>
);

const ExecutiveReport: React.FC = () => {
  const [report, setReport] = useState<ExecutiveReportType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    reportsApi.getExecutive()
      .then(res => setReport(res.data))
      .catch(_err => setReport(MOCK_EXECUTIVE_REPORT))  // fallback to demo data
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
      <CircularProgress size={60} />
    </Box>
  );
  if (error) return <Alert severity="error" sx={{ m: 3 }}>{error}</Alert>;
  if (!report) return null;

  const buChartData = report.business_unit_breakdown.map(b => ({
    name: b.business_unit || "Unknown",
    coverage: b.avg_coverage,
    count: b.count,
  }));

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight={700} color="primary">
            Executive Report
          </Typography>
          <Typography color="text.secondary">
            Generated: {new Date(report.generated_at).toLocaleString()}
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Download />} size="large">
          Download PDF
        </Button>
      </Box>

      {/* Recommendation Banner */}
      <Box mb={3} display="flex" justifyContent="center">
        <RecommendationBadge text={report.recommendation} />
      </Box>

      {/* Summary Metrics */}
      <Grid container spacing={2} mb={3}>
        {[
          { label: "Applications Scanned", value: report.applications_scanned },
          { label: "Applications Tested", value: report.applications_tested },
          { label: "Tests Executed", value: report.tests_executed.toLocaleString() },
          { label: "Tests Passed", value: report.tests_passed.toLocaleString() },
          { label: "Tests Failed", value: report.tests_failed.toLocaleString() },
          { label: "Pass Rate", value: `${report.pass_rate.toFixed(1)}%` },
          { label: "Coverage", value: `${report.coverage_percent.toFixed(1)}%` },
          { label: "Confidence Score", value: `${(report.confidence_score * 100).toFixed(0)}%` },
        ].map((item) => (
          <Grid item xs={6} sm={3} key={item.label}>
            <Paper elevation={1} sx={{ p: 2, borderRadius: 2, textAlign: "center" }}>
              <Typography variant="h5" fontWeight={700} color="primary">
                {item.value}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {item.label}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* Risk Level */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, borderRadius: 3, display: "flex", alignItems: "center", gap: 3 }}>
        <Box>
          <Typography variant="overline" color="text.secondary">Risk Level</Typography>
          <Box>
            <Chip
              label={report.risk_level}
              sx={{
                bgcolor: riskColors[report.risk_level] ?? "#1a237e",
                color: "white",
                fontWeight: 700,
                fontSize: "1rem",
                px: 2,
                height: 40,
              }}
            />
          </Box>
        </Box>
        <Divider orientation="vertical" flexItem />
        <Box flex={1}>
          <Typography variant="overline" color="text.secondary">Migration Readiness</Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <LinearProgress
              variant="determinate"
              value={report.migration_readiness}
              sx={{ flex: 1, height: 10, borderRadius: 5 }}
              color={report.migration_readiness >= 70 ? "success" : "warning"}
            />
            <Typography variant="h6" fontWeight={700}>
              {report.migration_readiness.toFixed(0)}%
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Score Gauges */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, borderRadius: 3 }}>
        <Typography variant="h6" fontWeight={600} mb={3}>Quality Scorecards</Typography>
        <Grid container justifyContent="space-around">
          <Grid item><ScoreGauge label="Security" value={report.security_score} color="#6a1b9a" /></Grid>
          <Grid item><ScoreGauge label="Performance" value={report.performance_score} color="#00838f" /></Grid>
          <Grid item><ScoreGauge label="Production Readiness" value={report.production_readiness} color="#1a237e" /></Grid>
          <Grid item><ScoreGauge label="Coverage" value={report.coverage_percent} color="#2e7d32" /></Grid>
          <Grid item><ScoreGauge label="Pass Rate" value={report.pass_rate} color="#f57c00" /></Grid>
        </Grid>
      </Paper>

      {/* Business Unit Breakdown */}
      {buChartData.length > 0 && (
        <Paper elevation={2} sx={{ p: 3, mb: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight={600} mb={2}>Coverage by Business Unit</Typography>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={buChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} unit="%" />
              <YAxis dataKey="name" type="category" width={120} />
              <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
              <Bar dataKey="coverage" radius={[0, 4, 4, 0]}>
                {buChartData.map((entry, i) => (
                  <Cell key={i} fill={entry.coverage >= 95 ? "#2e7d32" : entry.coverage >= 80 ? "#f57c00" : "#c62828"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      )}

      {/* API Type Breakdown */}
      <Paper elevation={2} sx={{ p: 3, borderRadius: 3 }}>
        <Typography variant="h6" fontWeight={600} mb={2}>Applications by API Classification</Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: "#f5f5f5" }}>
                <TableCell><strong>API Type</strong></TableCell>
                <TableCell align="right"><strong>Count</strong></TableCell>
                <TableCell><strong>Classification</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {report.api_type_breakdown.map((row) => (
                <TableRow key={row.api_type} hover>
                  <TableCell sx={{ textTransform: "capitalize" }}>{row.api_type}</TableCell>
                  <TableCell align="right">{row.count}</TableCell>
                  <TableCell>
                    <Chip
                      label={
                        row.api_type === "system" ? "System API (Layer 1)" :
                        row.api_type === "process" ? "Process API (Layer 2)" :
                        row.api_type === "experience" ? "Experience API (Layer 3)" : "Uncategorized"
                      }
                      size="small"
                      color={
                        row.api_type === "experience" ? "primary" :
                        row.api_type === "process" ? "secondary" : "default"
                      }
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default ExecutiveReport;
