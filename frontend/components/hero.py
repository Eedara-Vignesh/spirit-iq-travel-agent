"""
frontend/components/hero.py
============================
Cinematic travel hero component with interactive JavaScript animations,
floating elements, live metric counters, and seamless CTA navigation.
"""

from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components


def render_hero() -> None:
    """Render the cinematic hero banner with JavaScript micro-interactions."""
    hero_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap" rel="stylesheet">
      <style>
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
        body {
          background: transparent;
          font-family: 'Plus Jakarta Sans', sans-serif;
          color: #F1F5F9;
          overflow: hidden;
        }
        .hero-container {
          position: relative;
          min-height: 380px;
          border-radius: 24px;
          padding: 40px 32px;
          background: linear-gradient(135deg, rgba(11, 19, 43, 0.95) 0%, rgba(17, 30, 56, 0.85) 100%);
          border: 1px solid rgba(0, 240, 255, 0.2);
          box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4), inset 0 0 60px rgba(0, 240, 255, 0.05);
          overflow: hidden;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }

        /* Ambient floating light orbs */
        .ambient-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(50px);
          pointer-events: none;
          z-index: 1;
          opacity: 0.5;
          animation: floatOrb 8s ease-in-out infinite alternate;
        }
        .orb-1 {
          width: 260px;
          height: 260px;
          top: -40px;
          right: -20px;
          background: radial-gradient(circle, rgba(0, 240, 255, 0.25) 0%, transparent 70%);
        }
        .orb-2 {
          width: 220px;
          height: 220px;
          bottom: -30px;
          left: 10%;
          background: radial-gradient(circle, rgba(99, 102, 241, 0.2) 0%, transparent 70%);
          animation-delay: -4s;
        }

        /* Floating travel icons (JS / CSS animated) */
        .floating-icon {
          position: absolute;
          font-size: 1.5rem;
          color: rgba(0, 240, 255, 0.4);
          pointer-events: none;
          z-index: 2;
          user-select: none;
          animation: floatIcon 6s ease-in-out infinite alternate;
        }
        .f-icon-1 { top: 35px; right: 18%; animation-duration: 7s; }
        .f-icon-2 { bottom: 45px; right: 8%; animation-duration: 5s; animation-delay: -2s; }
        .f-icon-3 { top: 55%; right: 28%; animation-duration: 8s; animation-delay: -1s; }

        .hero-content {
          position: relative;
          z-index: 3;
          max-width: 720px;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 6px 16px;
          border-radius: 999px;
          background: rgba(0, 240, 255, 0.12);
          border: 1px solid rgba(0, 240, 255, 0.35);
          color: #00F0FF;
          font-size: 0.8rem;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          margin-bottom: 18px;
          animation: slideDown 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        .hero-headline {
          font-family: 'Outfit', sans-serif;
          font-size: clamp(2rem, 4.2vw, 3.2rem);
          font-weight: 800;
          line-height: 1.15;
          letter-spacing: -0.03em;
          color: #FFFFFF;
          margin-bottom: 16px;
          animation: slideDown 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        .hero-headline .highlight {
          background: linear-gradient(135deg, #00F0FF 0%, #06D6A0 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .hero-subhead {
          font-size: 1.05rem;
          line-height: 1.6;
          color: #94A3B8;
          margin-bottom: 28px;
          max-width: 650px;
          animation: slideDown 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        /* Metric counters grid */
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          max-width: 680px;
          animation: slideUp 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        @media (max-width: 680px) {
          .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        .metric-card {
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 14px;
          padding: 12px 14px;
          transition: all 0.25s ease;
        }

        .metric-card:hover {
          border-color: rgba(0, 240, 255, 0.4);
          background: rgba(0, 240, 255, 0.06);
          transform: translateY(-2px);
        }

        .metric-val {
          font-family: 'Outfit', sans-serif;
          font-size: 1.4rem;
          font-weight: 800;
          color: #00F0FF;
          display: flex;
          align-items: baseline;
          gap: 2px;
        }

        .metric-label {
          font-size: 0.75rem;
          color: #94A3B8;
          margin-top: 2px;
          font-weight: 500;
        }

        @keyframes floatOrb {
          0% { transform: translateY(0) scale(1); }
          100% { transform: translateY(-20px) scale(1.08); }
        }

        @keyframes floatIcon {
          0% { transform: translateY(0) rotate(0deg); }
          100% { transform: translateY(-16px) rotate(12deg); }
        }

        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-14px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(14px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @media (prefers-reduced-motion: reduce) {
          *, ::before, ::after {
            animation: none !important;
            transition: none !important;
          }
        }
      </style>
    </head>
    <body>
      <div class="hero-container">
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
        
        <div class="floating-icon f-icon-1">✈️</div>
        <div class="floating-icon f-icon-2">🧭</div>
        <div class="floating-icon f-icon-3">📍</div>

        <div class="hero-content">
          <div class="badge">
            <span>✨</span> Next-Gen AI Travel Architect
          </div>

          <h1 class="hero-headline">
            Your next adventure, <br><span class="highlight">intelligently planned.</span>
          </h1>

          <p class="hero-subhead">
            Experience AI-powered destination discovery, dynamic day-wise itineraries,
            real-time weather intelligence, Dijkstra shortest-path highway routing, and 
            bulletproof budget auditing in seconds.
          </p>

          <div class="metrics-grid">
            <div class="metric-card">
              <div class="metric-val" id="counter-dest">0+</div>
              <div class="metric-label">Curated Destinations</div>
            </div>
            <div class="metric-card">
              <div class="metric-val" id="counter-route">0</div>
              <div class="metric-label">Dijkstra Corridor Engine</div>
            </div>
            <div class="metric-card">
              <div class="metric-val" id="counter-weather">100%</div>
              <div class="metric-label">Live Weather Sync</div>
            </div>
            <div class="metric-card">
              <div class="metric-val" id="counter-budget">₹0</div>
              <div class="metric-label">Budget Precision</div>
            </div>
          </div>
        </div>
      </div>

      <script>
        // Smooth Number Counter Animation
        function animateCounter(id, target, suffix = '', duration = 1200) {
          const el = document.getElementById(id);
          if (!el) return;
          let start = 0;
          const stepTime = 25;
          const steps = duration / stepTime;
          const increment = target / steps;
          let current = 0;

          const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
              clearInterval(timer);
              el.innerText = target + suffix;
            } else {
              el.innerText = Math.floor(current) + suffix;
            }
          }, stepTime);
        }

        // Trigger counters upon load
        window.addEventListener('DOMContentLoaded', () => {
          setTimeout(() => {
            animateCounter('counter-dest', 24, '+', 1000);
            animateCounter('counter-route', 1, ' Hub', 800);
            animateCounter('counter-budget', 4, '-Tier', 1200);
          }, 200);
        });
      </script>
    </body>
    </html>
    """

    if hasattr(st, "iframe"):
        st.iframe(hero_html, height=420)
    else:
        components.html(hero_html, height=420)
