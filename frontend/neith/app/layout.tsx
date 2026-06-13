import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEITH — The Temple Awakens",
  description: "Network Entity Intelligence & Threat Hunter",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const hieroglyphs = [
    { glyph: "𓂀", top: "5%",  left: "3%",  delay: "0s",  size: "52px" },
    { glyph: "𓊹", top: "8%",  right: "4%", delay: "1.2s", size: "44px" },
    { glyph: "𓅃", top: "25%", left: "1%",  delay: "2.4s", size: "38px" },
    { glyph: "𓆑", top: "30%", right: "2%", delay: "0.8s", size: "48px" },
    { glyph: "𓄿", top: "50%", left: "2%",  delay: "3.6s", size: "42px" },
    { glyph: "𓃭", top: "55%", right: "3%", delay: "1.8s", size: "56px" },
    { glyph: "𓂀", top: "70%", left: "4%",  delay: "4.2s", size: "36px" },
    { glyph: "𓇳", top: "72%", right: "5%", delay: "2.8s", size: "46px" },
    { glyph: "𓊽", top: "88%", left: "6%",  delay: "5s",   size: "40px" },
    { glyph: "𓅓", top: "90%", right: "4%", delay: "3.2s", size: "50px" },
    { glyph: "𓆣", top: "15%", left: "92%", delay: "1.5s", size: "34px" },
    { glyph: "𓋴", top: "40%", left: "95%", delay: "4.8s", size: "44px" },
    { glyph: "𓈖", top: "65%", left: "93%", delay: "2.2s", size: "38px" },
    { glyph: "𓂝", top: "18%", left: "48%", delay: "5.5s", size: "28px" },
    { glyph: "𓃀", top: "82%", left: "50%", delay: "3.8s", size: "32px" },
  ];

  return (
    <html lang="en">
      <body>
        {/* Deep Background Layers */}
        <div style={{
          position: "fixed", top: 0, left: 0,
          width: "100%", height: "100%", zIndex: -3,
          background: `
            radial-gradient(circle at 50% 10%, rgba(187,104,48,0.07) 0%, transparent 55%),
            radial-gradient(circle at 85% 85%, rgba(40,65,57,0.18) 0%, transparent 50%),
            radial-gradient(circle at 15% 70%, rgba(133,67,30,0.06) 0%, transparent 40%),
            radial-gradient(circle at 70% 30%, rgba(52,30,15,0.1) 0%, transparent 45%)
          `,
          pointerEvents: "none",
        }} />

        {/* Noise Texture Overlay */}
        <div style={{
          position: "fixed", top: 0, left: 0,
          width: "100%", height: "100%", zIndex: -2,
          opacity: 0.015,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          pointerEvents: "none",
        }} />

        {/* Scan Line */}
        <div style={{
          position: "fixed", top: 0, left: 0,
          width: "100%", height: "2px",
          background: "linear-gradient(90deg, transparent, rgba(187,104,48,0.3), transparent)",
          zIndex: 100, pointerEvents: "none",
        }} className="animate-scan" />

        {/* Sacred Geometry Mandala */}
        <div className="animate-breathe" style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          width: "900px", height: "900px",
          zIndex: -1, pointerEvents: "none",
        }}>
          <svg width="900" height="900" xmlns="http://www.w3.org/2000/svg">
            <g stroke="#F8E794" fill="none" strokeWidth="0.6">
              <circle cx="450" cy="450" r="430" />
              <circle cx="450" cy="450" r="360" />
              <circle cx="450" cy="450" r="290" />
              <circle cx="450" cy="450" r="220" />
              <circle cx="450" cy="450" r="150" />
              <circle cx="450" cy="450" r="80" />
              <polygon points="450,25 810,650 90,650" />
              <polygon points="450,875 90,250 810,250" />
              <line x1="450" y1="20" x2="450" y2="880" />
              <line x1="20" y1="450" x2="880" y2="450" />
              <line x1="100" y1="100" x2="800" y2="800" />
              <line x1="800" y1="100" x2="100" y2="800" />
              <circle cx="450" cy="450" r="430" strokeDasharray="4 8" />
              <circle cx="450" cy="450" r="290" strokeDasharray="2 12" />
              {/* Inner star */}
              <polygon points="450,170 520,350 700,350 555,460 610,640 450,530 290,640 345,460 200,350 380,350" />
            </g>
          </svg>
        </div>

        {/* Hieroglyphs — Dense Forest */}
        {hieroglyphs.map((h, i) => (
          <div key={i} className="animate-hiero" style={{
            position: "fixed",
            top: (h as any).top,
            left: (h as any).left,
            right: (h as any).right,
            fontSize: h.size,
            color: "#F8E794",
            pointerEvents: "none",
            zIndex: -1,
            fontFamily: "serif",
            animationDelay: h.delay,
          }}>
            {h.glyph}
          </div>
        ))}

        {children}
      </body>
    </html>
  );
}