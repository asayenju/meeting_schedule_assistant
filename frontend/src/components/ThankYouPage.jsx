import React from "react";
import { motion } from "framer-motion";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import { useNavigate } from "react-router-dom";


export default function ThankYouPage({ userName = "" }) {
    const navigate = useNavigate();
    const onHome = () => {
        navigate("/");
    }
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(to bottom right, #e3f2fd, #fff9c4)",
        padding: 40,
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{ width: "100%", maxWidth: 540 }}
      >
        <Card elevation={8} style={{ borderRadius: 22, backdropFilter: "blur(6px)" }}>
          <CardContent style={{ padding: 36, textAlign: "center" }}>
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.4 }}
            >
              <SmartToyIcon style={{ fontSize: 86, color: "#4fc3f7", marginBottom: 14 }} />
            </motion.div>

            <Typography variant="h6" color="text.secondary" gutterBottom>
  {userName ? `${userName}, ` : ""}BMO appreciates you. Your meetings are in good hands.
</Typography>



<Typography color="text.secondary">
  BMO will continue monitoring your inbox, detecting meeting requests,
  helping you respond, and keeping your schedule organized.
</Typography>
<Box 
  display="flex" 
  gap={1.5} 
  justifyContent="center" 
  flexWrap="wrap"
  style={{ marginTop: 32, marginBottom: 32 }}
>
  <Button
    variant="outlined"
    size="large"
    onClick={onHome}
    style={{ padding: "14px 28px", borderRadius: 16 }}
  >
    Back to Home
  </Button>
</Box>

          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}