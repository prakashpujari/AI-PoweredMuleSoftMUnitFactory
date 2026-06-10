import React, { useEffect, useState } from "react";
import {
  Box, Typography, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Select, MenuItem, FormControl, InputLabel,
  Alert, CircularProgress, Chip, LinearProgress, IconButton, Tooltip,
} from "@mui/material";
import { DataGrid, GridColDef, GridRenderCellParams } from "@mui/x-data-grid";
import { Add, Refresh, PlayArrow, Assessment } from "@mui/icons-material";
import { applicationsApi, munitApi, executionApi } from "../services/api";
import { MOCK_APPLICATIONS } from "../services/mockData";
import type { Application } from "../types";

const StatusChip: React.FC<{ status: string }> = ({ status }) => {
  const colorMap: Record<string, "success" | "warning" | "error" | "info" | "default"> = {
    tested: "success",
    analyzed: "info",
    discovered: "default",
    generating: "warning",
    failed: "error",
  };
  return <Chip label={status} size="small" color={colorMap[status] ?? "default"} />;
};

const ScoreBar: React.FC<{ value: number }> = ({ value }) => (
  <Box display="flex" alignItems="center" gap={1} width="100%">
    <LinearProgress
      variant="determinate"
      value={Math.min(value, 100)}
      sx={{ flex: 1, height: 8, borderRadius: 4 }}
      color={value >= 90 ? "success" : value >= 70 ? "warning" : "error"}
    />
    <Typography variant="caption" minWidth={35}>{value.toFixed(0)}%</Typography>
  </Box>
);

const Applications: React.FC = () => {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
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
    } catch (_e: any) {
      setApps(MOCK_APPLICATIONS);  // fallback to demo data
    } finally {
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
    } catch (e: any) {
      setError(e.response?.data?.message ?? "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  const handleGenerateTests = async (appId: string) => {
    try {
      await munitApi.generate({ application_id: appId, ai_provider: "groq" });
      setSuccess("MUnit tests generated successfully");
      fetchApps();
    } catch (e: any) {
      setError(e.response?.data?.message ?? "Test generation failed");
    }
  };

  const handleExecute = async (appId: string) => {
    try {
      await executionApi.run({ application_id: appId });
      setSuccess("Test execution started");
      fetchApps();
    } catch (e: any) {
      setError(e.response?.data?.message ?? "Execution failed");
    }
  };

  const columns: GridColDef<Application>[] = [
    { field: "name", headerName: "Application", width: 200, renderCell: (p) => (
      <Typography variant="body2" fontWeight={600}>{p.value}</Typography>
    )},
    { field: "mule_runtime_version", headerName: "Runtime", width: 100 },
    { field: "api_type", headerName: "API Type", width: 110, renderCell: (p) => (
      <Chip label={p.value?.toUpperCase()} size="small" variant="outlined" />
    )},
    { field: "status", headerName: "Status", width: 110, renderCell: (p) => (
      <StatusChip status={p.value} />
    )},
    { field: "flows_count", headerName: "Flows", width: 80, type: "number" },
    { field: "coverage_score", headerName: "Coverage", width: 160, renderCell: (p) => (
      <ScoreBar value={p.value ?? 0} />
    )},
    { field: "production_readiness_score", headerName: "Readiness", width: 160, renderCell: (p) => (
      <ScoreBar value={p.value ?? 0} />
    )},
    { field: "business_unit", headerName: "Business Unit", width: 140 },
    { field: "environment", headerName: "Environment", width: 120 },
    {
      field: "actions",
      headerName: "Actions",
      width: 140,
      sortable: false,
      renderCell: (p: GridRenderCellParams<Application>) => (
        <Box display="flex" gap={0.5}>
          <Tooltip title="Generate MUnit Tests">
            <IconButton size="small" color="primary" onClick={() => handleGenerateTests(p.row.id)}>
              <Add fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Execute Tests">
            <IconButton size="small" color="success" onClick={() => handleExecute(p.row.id)}>
              <PlayArrow fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="View Report">
            <IconButton size="small" color="secondary">
              <Assessment fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={700}>Applications</Typography>
        <Box display="flex" gap={2}>
          <Button startIcon={<Refresh />} onClick={fetchApps} variant="outlined">
            Refresh
          </Button>
          <Button startIcon={<Add />} variant="contained" onClick={() => setScanDialogOpen(true)}>
            Scan Application
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

      <DataGrid
        rows={apps}
        columns={columns}
        loading={loading}
        initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        pageSizeOptions={[25, 50, 100]}
        disableRowSelectionOnClick
        sx={{ height: 600, borderRadius: 3 }}
      />

      {/* Scan Dialog */}
      <Dialog open={scanDialogOpen} onClose={() => setScanDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Scan MuleSoft Application</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <TextField
              label="Repository Path"
              value={scanForm.repo_path}
              onChange={e => setScanForm(f => ({ ...f, repo_path: e.target.value }))}
              placeholder="/path/to/mule-project"
              required
              fullWidth
            />
            <TextField
              label="Business Unit"
              value={scanForm.business_unit}
              onChange={e => setScanForm(f => ({ ...f, business_unit: e.target.value }))}
              fullWidth
            />
            <TextField
              label="Domain"
              value={scanForm.domain}
              onChange={e => setScanForm(f => ({ ...f, domain: e.target.value }))}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>API Type</InputLabel>
              <Select value={scanForm.api_type} onChange={e => setScanForm(f => ({ ...f, api_type: e.target.value }))}>
                <MenuItem value="system">System API</MenuItem>
                <MenuItem value="process">Process API</MenuItem>
                <MenuItem value="experience">Experience API</MenuItem>
                <MenuItem value="unknown">Unknown</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>AI Provider</InputLabel>
              <Select value={scanForm.ai_provider} onChange={e => setScanForm(f => ({ ...f, ai_provider: e.target.value }))}>
                <MenuItem value="groq">Groq (llama-3.3-70b)</MenuItem>
                <MenuItem value="anthropic">Claude (Anthropic)</MenuItem>
                <MenuItem value="openai">GPT-4o (OpenAI)</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScanDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleScan} variant="contained" disabled={!scanForm.repo_path || scanning}>
            {scanning ? <CircularProgress size={20} /> : "Scan"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Applications;
