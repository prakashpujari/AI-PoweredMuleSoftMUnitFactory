import React from "react";
import { Card, CardContent, Typography, Box, LinearProgress, Tooltip } from "@mui/material";
import { SvgIconComponent } from "@mui/icons-material";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactElement;
  color?: string;
  progress?: number;
  progressColor?: "primary" | "secondary" | "error" | "warning" | "info" | "success";
  tooltip?: string;
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color = "#1a237e",
  progress,
  progressColor = "primary",
  tooltip,
}) => {
  const card = (
    <Card
      elevation={2}
      sx={{
        borderRadius: 3,
        borderLeft: `4px solid ${color}`,
        transition: "transform 0.2s, box-shadow 0.2s",
        "&:hover": { transform: "translateY(-2px)", boxShadow: 6 },
        height: "100%",
      }}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Typography variant="overline" color="text.secondary" fontWeight={600} fontSize="0.7rem">
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={700} color={color} sx={{ my: 0.5 }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          {icon && (
            <Box
              sx={{
                bgcolor: `${color}18`,
                borderRadius: 2,
                p: 1,
                display: "flex",
                alignItems: "center",
              }}
            >
              {React.cloneElement(icon, { sx: { color, fontSize: 32 } } as any)}
            </Box>
          )}
        </Box>
        {progress !== undefined && (
          <Box mt={1.5}>
            <LinearProgress
              variant="determinate"
              value={Math.min(progress, 100)}
              color={progressColor}
              sx={{ height: 6, borderRadius: 3 }}
            />
            <Typography variant="caption" color="text.secondary" mt={0.5}>
              {progress.toFixed(1)}%
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  return tooltip ? <Tooltip title={tooltip}>{card}</Tooltip> : card;
};

export default KPICard;
