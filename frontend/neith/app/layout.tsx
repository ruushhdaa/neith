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
  return (
    <html lang="en">
      <body>
        {/* Sacred Background Gradients */}
        <div style={{
          position: "fixed", top: 0, left: 0,
          width: "100%", height: "100%", zIndex: -2,
          background: `
            radial-gradient(circle at 50% 10%, rgba(187,104,48,0.07) 0%, transparent 55%),
            radial-gradient(circle at 85% 85%, rgba(40,65,57,0.18) 0%, transparent 50%)
          `,
          pointerEvents: "none",
        }} />

        {/* Scan Line — a thin amber line that scrolls down the page slowly */}
        <div style={{
          position: "fixed", top: 0, left: 0,
          width: "100%", height: "2px",
          background: "linear-gradient(90deg, transparent, rgba(187,104,48,0.3), transparent)",
          zIndex: 100, pointerEvents: "none",
        }} className="animate-scan" />

        {/* Sacred Geometry Mandala — breathing */}
        <div className="animate-breathe" style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          width: "800px", height: "800px",
          zIndex: -1, pointerEvents: "none",
        }}>
          <svg width="800" height="800" xmlns="http://www.w3.org/2000/svg">
            <g stroke="#F8E794" fill="none" strokeWidth="0.8">
              <circle cx="400" cy="400" r="380" />
              <circle cx="400" cy="400" r="300" />
              <circle cx="400" cy="400" r="220" />
              <circle cx="400" cy="400" r="140" />
              <circle cx="400" cy="400" r="60" />
              <polygon points="400,30 745,600 55,600" />
              <polygon points="400,770 55,200 745,200" />
              <line x1="400" y1="20" x2="400" y2="780" />
              <line x1="20" y1="400" x2="780" y2="400" />
              <line x1="110" y1="110" x2="690" y2="690" />
              <line x1="690" y1="110" x2="110" y2="690" />
              <circle cx="400" cy="400" r="380" strokeDasharray="4 8" />
            </g>
          </svg>
        </div>

        {/* Breathing Hieroglyphs */}
        {[
          { glyph: "𓂀", top: "8%",  left: "4%",  delay: "0s" },
          { glyph: "𓊹", top: "12%", right: "5%", delay: "1s" },
          { glyph: "𓅃", top: "50%", left: "2%",  delay: "2s" },
          { glyph: "𓆑", top: "55%", right: "3%", delay: "3s" },
          { glyph: "𓄿", bottom: "10%", left: "6%", delay: "4s" },
          { glyph: "𓂀", bottom: "8%",  right: "7%", delay: "5s" },
        ].map((h, i) => (
          <div key={i} className="animate-hiero" style={{
            position: "fixed",
            top: (h as any).top,
            left: (h as any).left,
            right: (h as any).right,
            bottom: (h as any).bottom,
            fontSize: "52px",
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
