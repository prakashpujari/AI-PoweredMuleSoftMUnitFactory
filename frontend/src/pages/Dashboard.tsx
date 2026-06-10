import React, { useEffect, useState } from "react";
import {
  Box, Grid, Typography, Alert, CircularProgress, Chip,
  Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Divider,
} from "@mui/material";
import {
  CheckCircle, Error, Speed, Security, Storage,
  Assessment, TrendingUp, CloudQueue, Warning,
} from "@mui/icons-material";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line,
} from "recharts";

import KPICard from "../components/dashboard/KPICard";
import { dashboardApi } from "../services/api";
import { MOCK_DASHBOARD } from "../services/mockData";
import type { DashboardData } from "../types";

const COLORS = ["#1a237e", "#0288d1", "#2e7d32", "#f57c00", "#c62828", "#6a1b9a"];

const getRiskColor = (level: string): "error" | "warning" | "success" | "default" => {
  switch (level?.toUpperCase()) {
    case "CRITICAL": return "error";
    case "HIGH": return "error";
    case "MEDIUM": return "warning";
    case "LOW": return "success";
    default: return "default";
  }
};

const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await dashboardApi.get();
        setData(res.data);
      } catch (_err: any) {
        // Fallback to demo data when API is unavailable
        setData(MOCK_DASHBOARD);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
      <CircularProgress size={60} />
    </Box>
  );

  if (error) return <Alert severity="error" sx={{ m: 3 }}>{error}</Alert>;
  if (!data) return null;

  const severityChartData = Object.entries(data.failures?.by_severity ?? {}).map(([k, v]) => ({
    severity: k.toUpperCase(),
    count: v,
  }));

  const apiTypeData = Object.entries(data.breakdown?.by_api_type ?? {}).map(([k, v]) => ({
    name: k.toUpperCase(),
    value: v,
  }));

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight={700} color="primary">
            AI-MUnit-Factory
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Enterprise MuleSoft Testing Platform — Executive Dashboard
          </Typography>
        </Box>
        <Chip
          label={`Last updated: ${new Date(data.generated_at).toLocaleTimeString()}`}
          size="small"
          color="primary"
          variant="outlined"
        />
      </Box>

      <Divider sx={{ mb: 3 }} />

      {/* KPI Row 1 — Applications & Tests */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Applications Scanned"
            value={data.applications.total_scanned}
            subtitle={`${data.applications.total_tested} tested`}
            icon={<CloudQueue />}
            color="#1a237e"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Tests Executed"
            value={data.tests.total_executed.toLocaleString()}
            subtitle={`${data.tests.passed.toLocaleString()} passed`}
            icon={<CheckCircle />}
            color="#2e7d32"
            progress={data.tests.pass_rate}
            progressColor="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Tests Failed"
            value={data.tests.failed.toLocaleString()}
            subtitle={`Pass rate: ${data.tests.pass_rate.toFixed(1)}%`}
            icon={<Error />}
            color={data.tests.failed > 0 ? "#c62828" : "#2e7d32"}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Coverage %"
            value={`${data.coverage.average_overall.toFixed(1)}%`}
            subtitle={`Target: ${data.coverage.target}%`}
            icon={<Assessment />}
            color="#f57c00"
            progress={data.coverage.average_overall}
            progressColor={data.coverage.average_overall >= 95 ? "success" : "warning"}
          />
        </Grid>
      </Grid>

      {/* KPI Row 2 — Scores */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Production Readiness"
            value={`${data.scores.production_readiness.toFixed(0)}/100`}
            icon={<TrendingUp />}
            color="#1565c0"
            progress={data.scores.production_readiness}
            progressColor="primary"
            tooltip="Weighted score based on test pass rate, coverage, and security"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Security Score"
            value={`${data.scores.security.toFixed(0)}/100`}
            icon={<Security />}
            color="#6a1b9a"
            progress={data.scores.security}
            progressColor="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Performance Score"
            value={`${data.scores.performance.toFixed(0)}/100`}
            icon={<Speed />}
            color="#00838f"
            progress={data.scores.performance}
            progressColor="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Risk Score"
            value={`${data.scores.risk.toFixed(0)}/100`}
            subtitle="Lower is better"
            icon={<Warning />}
            color={data.scores.risk > 50 ? "#c62828" : data.scores.risk > 25 ? "#f57c00" : "#2e7d32"}
            progress={data.scores.risk}
            progressColor={data.scores.risk > 50 ? "error" : data.scores.risk > 25 ? "warning" : "success"}
            tooltip="Risk score (0=no risk, 100=critical risk)"
          />
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} mb={3}>
        {/* Failure Severity Chart */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight={600} mb={2}>
              Failure Severity Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={severityChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="severity" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#1a237e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* API Type Pie */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="h6" fontWeight={600} mb={2}>
              Applications by API Type
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={apiTypeData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {apiTypeData.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Test Runs Table */}
      <Paper elevation={2} sx={{ borderRadius: 3 }}>
        <Box p={3} pb={1}>
          <Typography variant="h6" fontWeight={600}>
            Recent Test Runs
          </Typography>
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: "#f5f5f5" }}>
                <TableCell><strong>Run #</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell align="right"><strong>Total</strong></TableCell>
                <TableCell align="right"><strong>Passed</strong></TableCell>
                <TableCell align="right"><strong>Failed</strong></TableCell>
                <TableCell align="right"><strong>Pass Rate</strong></TableCell>
                <TableCell><strong>Date</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(data.recent_runs ?? []).map((run) => (
                <TableRow key={run.id} hover>
                  <TableCell>#{run.run_number}</TableCell>
                  <TableCell>
                    <Chip
                      label={run.status}
                      size="small"
                      color={run.status === "completed" ? "success" : run.status === "failed" ? "error" : "warning"}
                    />
                  </TableCell>
                  <TableCell align="right">{run.total}</TableCell>
                  <TableCell align="right" sx={{ color: "success.main" }}>{run.passed}</TableCell>
                  <TableCell align="right" sx={{ color: run.failed > 0 ? "error.main" : "inherit" }}>
                    {run.failed}
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={`${run.pass_rate.toFixed(1)}%`}
                      size="small"
                      color={run.pass_rate >= 95 ? "success" : run.pass_rate >= 80 ? "warning" : "error"}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{new Date(run.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
              {(data.recent_runs ?? []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 3, color: "text.secondary" }}>
                    No test runs yet. Start by scanning an application.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default Dashboard;
