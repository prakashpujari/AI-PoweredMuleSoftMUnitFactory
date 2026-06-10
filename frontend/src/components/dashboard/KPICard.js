import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import React from "react";
import { Card, CardContent, Typography, Box, LinearProgress, Tooltip } from "@mui/material";
const KPICard = ({ title, value, subtitle, icon, color = "#1a237e", progress, progressColor = "primary", tooltip, }) => {
    const card = (_jsx(Card, { elevation: 2, sx: {
            borderRadius: 3,
            borderLeft: `4px solid ${color}`,
            transition: "transform 0.2s, box-shadow 0.2s",
            "&:hover": { transform: "translateY(-2px)", boxShadow: 6 },
            height: "100%",
        }, children: _jsxs(CardContent, { children: [_jsxs(Box, { display: "flex", justifyContent: "space-between", alignItems: "flex-start", children: [_jsxs(Box, { flex: 1, children: [_jsx(Typography, { variant: "overline", color: "text.secondary", fontWeight: 600, fontSize: "0.7rem", children: title }), _jsx(Typography, { variant: "h4", fontWeight: 700, color: color, sx: { my: 0.5 }, children: value }), subtitle && (_jsx(Typography, { variant: "body2", color: "text.secondary", children: subtitle }))] }), icon && (_jsx(Box, { sx: {
                                bgcolor: `${color}18`,
                                borderRadius: 2,
                                p: 1,
                                display: "flex",
                                alignItems: "center",
                            }, children: React.cloneElement(icon, { sx: { color, fontSize: 32 } }) }))] }), progress !== undefined && (_jsxs(Box, { mt: 1.5, children: [_jsx(LinearProgress, { variant: "determinate", value: Math.min(progress, 100), color: progressColor, sx: { height: 6, borderRadius: 3 } }), _jsxs(Typography, { variant: "caption", color: "text.secondary", mt: 0.5, children: [progress.toFixed(1), "%"] })] }))] }) }));
    return tooltip ? _jsx(Tooltip, { title: tooltip, children: card }) : card;
};
export default KPICard;
