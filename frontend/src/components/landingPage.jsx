import React from "react";
import { motion } from "framer-motion";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import SmartToyIcon from "@mui/icons-material/SmartToy"; // BMO-like icon
import ScheduleIcon from "@mui/icons-material/Schedule";
import EmailIcon from "@mui/icons-material/Email";
import ChatIcon from "@mui/icons-material/Chat";
import { signInWithGoogle } from "../api/auth_api";

export default function LandingPage() {
  const handleGoogleSignIn = () => {
    signInWithGoogle();
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(to bottom right, #e3f2fd, #fff9c4)",
        padding: "40px",
      }}
    >
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        style={{ textAlign: "center", maxWidth: "650px", marginBottom: "60px" }}
      >
        <Typography variant="h3" fontWeight="bold" gutterBottom>
          Meet BMO — Your Baby Meeting Organizer
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Inspired by Adventure Time's BMO, your AI friend who reads your Gmail,
          detects meeting requests, helps you respond, schedules events, and keeps
          your day organized.
        </Typography>
      </motion.div>

      {/* Sign-In Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        style={{ width: "100%", maxWidth: "420px" }}
      >
        <Card elevation={6} style={{ borderRadius: "20px", backdropFilter: "blur(5px)" }}>
          <CardContent style={{ padding: "32px", textAlign: "center" }}>
            <motion.div
              initial={{ opacity: 0, scale: 0.7 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
            >
              <SmartToyIcon style={{ fontSize: 80, color: "#4fc3f7", marginBottom: 20 }} />
            </motion.div>

            <Typography variant="h5" fontWeight="600" gutterBottom>
              Ready to Meet BMO?
            </Typography>
            <Typography color="text.secondary" style={{ marginBottom: "30px" }}>
              Sign in with Google to activate your personal organizing companion.
            </Typography>

            <Button
              onClick={handleGoogleSignIn}
              variant="contained"
              size="large"
              style={{ padding: "14px 32px", borderRadius: "14px" }}
            >
              Sign in with Google
            </Button>
          </CardContent>
        </Card>
      </motion.div>

      {/* Features Section – More organized, cleaner layout */}
     {/* Features Section – Organized into two balanced columns */}
<motion.div
initial={{ opacity: 0, y: 20 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.8, delay: 0.3 }}
style={{ width: "100%", display: "flex", justifyContent: "center", marginTop: "80px" }}
>
<Box
display="flex"
flexDirection={{ xs: "column", md: "row" }}
justifyContent="center"
alignItems="stretch"
gap={4}
width="100%"
maxWidth="1000px"
>
{/* Left Column */}
<Box display="flex" flexDirection="column" gap={4} flex={1}>
{[
{
icon: <EmailIcon style={{ fontSize: 45, color: "#42a5f5" }} />,
title: "Email Monitoring",
desc: "BMO reads your inbox and detects meeting requests instantly.",
},
{
icon: <ChatIcon style={{ fontSize: 45, color: "#66bb6a" }} />,
title: "Talk to BMO",
desc: "Approve, decline, or reschedule by simply chatting with BMO.",
},
].map((f, idx) => (
<Card key={idx} elevation={5} style={{ padding: "28px", borderRadius: "20px" }}>
<Box display="flex" alignItems="center" gap={2} marginBottom={2}>
{f.icon}
<Typography variant="h6" fontWeight="700">
{f.title}
</Typography>
</Box>
<Typography color="text.secondary">{f.desc}</Typography>
</Card>
))}
</Box>


{/* Right Column */}
<Box display="flex" flexDirection="column" gap={4} flex={1}>
{[
{
icon: <ScheduleIcon style={{ fontSize: 45, color: "#ab47bc" }} />,
title: "Smart Scheduling",
desc: "If you approve, BMO adds the meeting directly to your Google Calendar.",
},
{
icon: <EmailIcon style={{ fontSize: 45, color: "#ffa726" }} />,
title: "Polite Auto-Replies",
desc: "If you're busy, BMO emails the person with your availability — automatically.",
},
].map((f, idx) => (
<Card key={idx} elevation={5} style={{ padding: "28px", borderRadius: "20px" }}>
<Box display="flex" alignItems="center" gap={2} marginBottom={2}>
{f.icon}
<Typography variant="h6" fontWeight="700">
{f.title}
</Typography>
</Box>
<Typography color="text.secondary">{f.desc}</Typography>
</Card>
))}
</Box>
</Box>
</motion.div>
    </div>
  );
}