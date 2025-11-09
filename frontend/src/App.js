import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import LandingPage from "./components/landingPage";
import ThankYouPage from "./components/ThankYouPage";
import VoiceAssistant from "./components/mic"; // 👈 add this import

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/thank-you" element={<ThankYouPage />} />
        <Route path="/voice" element={<VoiceAssistant />} /> {/* 👈 new route */}
      </Routes>
    </Router>
  );
}
