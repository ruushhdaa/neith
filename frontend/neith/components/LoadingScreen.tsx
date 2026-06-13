"use client";

import { useState, useEffect } from "react";

const phrases = [
  "The temple stirs...",
  "Carving the sacred glyphs...",
  "Weaving the threads of the network...",
  "The eye of Neith opens...",
  "Summoning the Graph Neural Network...",
  "Reading the CICIDS scrolls...",
  "Neith perceives the flow of data...",
  "The goddess awakens...",
];

export default function LoadingScreen() {
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [dotCount, setDotCount] = useState(0);

  useEffect(() => {
    const phraseInterval = setInterval(() => {
      setPhraseIndex(i => (i + 1) % phrases.length);
    }, 2500);

    const dotInterval = setInterval(() => {
      setDotCount(d => (d + 1) % 4);
    }, 500);

    return () => {
      clearInterval(phraseInterval);
      clearInterval(dotInterval);
    };
  }, []);

  const dots = ".".repeat(dotCount);

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: "32px",
    }}>
      {/* Large Eye */}
      <div className="animate-breathe" style={{ fontSize: "72px", lineHeight: 1 }}>
        𓂀
      </div>

      {/* NEITH title */}
      <h1 className="font-temple animate-flicker" style={{
        fontSize: "56px",
        color: "#F8E794",
        textShadow: "0 0 40px rgba(248,231,148,0.25)",
      }}>
        NEITH
      </h1>

      {/* Rotating phrase */}
      <p className="font-scroll" style={{
        fontSize: "18px",
        color: "#809070",
        minHeight: "30px",
        textAlign: "center",
      }}>
        {phrases[phraseIndex]}{dots}
      </p>

      {/* Scanning bar */}
      <div style={{
        width: "200px",
        height: "2px",
        background: "rgba(187,104,48,0.2)",
        overflow: "hidden",
        marginTop: "16px",
      }}>
        <div style={{
          width: "60px",
          height: "100%",
          background: "linear-gradient(90deg, transparent, #BB6830, transparent)",
        }} className="animate-scan" />
      </div>

      {/* Status text */}
      <span className="font-carved" style={{ fontSize: "9px", color: "#341E0F" }}>
        Establishing connection to the mortal plane
      </span>
    </div>
  );
}
