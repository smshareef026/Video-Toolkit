import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  interpolate,
  random,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { continueRender, delayRender } from "remotion";
import { PAGES, Word } from "./captions";
import { CINZEL_WOFF2 } from "./font";

// Font is embedded (the render browser can't reach Google Fonts from this environment).
const fontFamily = "CinzelLocal";
const useCinzel = () => {
  const [handle] = React.useState(() => delayRender("Loading Cinzel"));
  React.useEffect(() => {
    const face = new FontFace(fontFamily, `url(${CINZEL_WOFF2}) format("woff2")`, { weight: "400 900" });
    face
      .load()
      .then((f) => {
        document.fonts.add(f);
        continueRender(handle);
      })
      .catch((err) => {
        console.error(err);
        continueRender(handle);
      });
  }, [handle]);
};

export const FPS = 30;
export const W = 1080;
export const H = 1920;
export const DURATION_S = 42.4;
const LOOP_END = 32.3;

const CRIMSON = "#C8283F";
const AMBER = "#F3D9A4";

// ---------------------------------------------------------------------------
// Camera plate: a still moved like a camera. Focal point (fx, fy) in 0..1 image
// coordinates is kept at frame centre (clamped so the frame stays covered).
// ---------------------------------------------------------------------------
type Move = {
  src: string;
  iw: number;
  ih: number;
  from: { fx: number; fy: number; s: number };
  to: { fx: number; fy: number; s: number };
  ease?: (t: number) => number;
  grade?: string;
};

const Plate: React.FC<Move & { frames: number }> = ({
  src, iw, ih, from, to, frames, ease = Easing.inOut(Easing.cubic), grade,
}) => {
  const f = useCurrentFrame();
  const t = ease(Math.min(1, Math.max(0, f / Math.max(1, frames - 1))));
  const lerp = (a: number, b: number) => a + (b - a) * t;
  const s = lerp(from.s, to.s);
  const fx = lerp(from.fx, to.fx);
  const fy = lerp(from.fy, to.fy);
  const base = Math.max(W / iw, H / ih);
  const dw = iw * base * s;
  const dh = ih * base * s;
  let x = W / 2 - fx * dw;
  let y = H / 2 - fy * dh;
  x = Math.min(0, Math.max(W - dw, x));
  y = Math.min(0, Math.max(H - dh, y));
  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>
      <Img
        src={staticFile(src)}
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: dw,
          height: dh,
          filter: grade ?? "sepia(0.1) saturate(0.6) contrast(1.2) brightness(0.84)",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Shot list (seconds, video timeline). Hard cuts only.
// ---------------------------------------------------------------------------
const BUST = { src: "bust.jpg", iw: 1661, ih: 2600 };
const BUST2 = { src: "bust2.jpg", iw: 875, ih: 1280 };
const DEC = { src: "decadence.jpg", iw: 2600, ih: 1553 };
const LEO = { src: "leopard.jpg", iw: 2600, ih: 1733 };
const LION = { src: "lion_leopard.jpg", iw: 1733, ih: 2600 };
const ROSES = { src: "roses.jpg", iw: 2600, ih: 1601 };
const XENIA = { src: "xenia2.jpg", iw: 2600, ih: 2555 };
const CALIGULA = { src: "caligula.jpg", iw: 1731, ih: 2600 };

const LOOP_FRAME = { fx: 0.5, fy: 0.36, s: 1.08 };

type Shot = Move & { start: number; end: number };
const SHOTS: Shot[] = [
  // HOOK — fast push into the marble eyes
  { ...BUST, start: 0, end: 5.4, from: LOOP_FRAME, to: { fx: 0.5, fy: 0.35, s: 1.9 },
    ease: Easing.out(Easing.cubic) },
  // "Elagabalus became emperor at fourteen" — the boy's face
  { ...BUST2, start: 5.4, end: 8.2, from: { fx: 0.5, fy: 0.42, s: 1.05 }, to: { fx: 0.5, fy: 0.36, s: 1.35 } },
  // "Drunk guests would wake up to…" — the orgy, creeping pan
  { ...DEC, start: 8.2, end: 9.63, from: { fx: 0.38, fy: 0.62, s: 1.25 }, to: { fx: 0.5, fy: 0.62, s: 1.3 } },
  // "…lions…"
  { ...LION, start: 9.63, end: 10.23, from: { fx: 0.52, fy: 0.45, s: 1.15 }, to: { fx: 0.52, fy: 0.42, s: 1.25 } },
  // "…and leopards lying next to them."
  { ...LEO, start: 10.23, end: 11.95, from: { fx: 0.47, fy: 0.42, s: 1.2 }, to: { fx: 0.5, fy: 0.4, s: 1.45 } },
  // "Some reportedly died of fright." — snap onto the teeth
  { ...LION, start: 11.95, end: 14.25, from: { fx: 0.52, fy: 0.4, s: 1.6 }, to: { fx: 0.5, fy: 0.37, s: 2.7 },
    ease: Easing.out(Easing.cubic) },
  // Fake feasts of wax and glass — the fresco of fish
  { ...XENIA, start: 14.25, end: 19.2, from: { fx: 0.5, fy: 0.5, s: 1.1 }, to: { fx: 0.56, fy: 0.55, s: 1.6 },
    grade: "sepia(0.08) saturate(0.75) contrast(1.2) brightness(0.85)" },
  // Roses — pan down from the emperor's couch to the drowning guests
  { ...ROSES, start: 19.2, end: 24.45, from: { fx: 0.6, fy: 0.18, s: 1.9 }, to: { fx: 0.28, fy: 0.85, s: 1.7 },
    ease: Easing.inOut(Easing.sin), grade: "sepia(0.06) saturate(0.7) contrast(1.15) brightness(0.85)" },
  // "By eighteen, his own guards had killed him." — cold, drained
  { ...BUST2, start: 24.45, end: 27.25, from: { fx: 0.5, fy: 0.4, s: 1.4 }, to: { fx: 0.5, fy: 0.34, s: 1.1 },
    grade: "grayscale(1) contrast(1.35) brightness(0.75)" },
  // "And the guests who survived… still had to come to dinner…"
  { ...DEC, start: 27.25, end: 31.25, from: { fx: 0.62, fy: 0.55, s: 1.15 }, to: { fx: 0.45, fy: 0.58, s: 1.25 },
    ease: Easing.linear },
  // "…with this Roman emperor—" → matches frame 0 exactly: the loop
  { ...BUST, start: 31.25, end: LOOP_END, from: { fx: 0.5, fy: 0.37, s: 1.0 }, to: LOOP_FRAME, ease: Easing.linear },
  // CTA — "I'm covering history's most chaotic rulers all week. Hit subscribe…"
  { ...ROSES, start: LOOP_END, end: 35.9, from: { fx: 0.35, fy: 0.6, s: 1.15 }, to: { fx: 0.6, fy: 0.45, s: 1.3 },
    ease: Easing.linear, grade: "sepia(0.06) saturate(0.7) contrast(1.15) brightness(0.8)" },
  { ...BUST, start: 35.9, end: 38.5, from: { fx: 0.5, fy: 0.36, s: 1.3 }, to: { fx: 0.5, fy: 0.38, s: 1.05 },
    grade: "sepia(0.1) saturate(0.6) contrast(1.2) brightness(0.76)" },
  // "…the emperor who tried to make his horse a politician." — tomorrow: Caligula
  { ...CALIGULA, start: 38.5, end: DURATION_S, from: { fx: 0.5, fy: 0.4, s: 1.05 }, to: { fx: 0.5, fy: 0.3, s: 1.6 },
    ease: Easing.out(Easing.cubic) },
];

// Impact flashes (seconds)
const FLASHES = [26.67, 11.95];

const Flash: React.FC = () => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 1, 5], [0.3, 0.18, 0], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ backgroundColor: AMBER, opacity: o, mixBlendMode: "screen" }} />;
};

// ---------------------------------------------------------------------------
// Texture: grain + vignette + warm light leak
// ---------------------------------------------------------------------------
const Grain: React.FC = () => {
  const f = useCurrentFrame();
  const seed = Math.floor(random(`g${f}`) * 1000);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width={W} height={H} style={{ position: "absolute", opacity: 0.16, mixBlendMode: "overlay" }}>
        <filter id="n">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={seed} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#n)" />
      </svg>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 75% 60% at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.55) 80%, rgba(0,0,0,0.9) 100%)",
        }}
      />
      <AbsoluteFill
        style={{
          background: "linear-gradient(180deg, rgba(40,18,0,0.25) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 70%, rgba(20,8,0,0.35) 100%)",
          mixBlendMode: "multiply",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Captions — Roman inscriptional capitals, word-by-word
// ---------------------------------------------------------------------------
const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const idx = PAGES.findIndex((p, i) => {
    const next = PAGES[i + 1];
    const end = next ? next[0].start : DURATION_S + 1;
    return t >= p[0].start - 0.05 && t < end;
  });
  if (idx < 0) return null;
  const page = PAGES[idx];
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: H * 0.58 }}>
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", width: W * 0.86, gap: "0 26px" }}>
        {page.map((w: Word, i: number) => {
          const startF = Math.round(w.start * fps);
          const shown = frame >= startF - 1;
          const pop = spring({ frame: frame - startF, fps, config: { damping: 200, stiffness: 120, mass: 0.8 } });
          const active = t >= w.start && t < w.end + 0.08;
          return (
            <span
              key={i}
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: w.text.length > 9 ? 84 : 100,
                lineHeight: 1.1,
                letterSpacing: 2,
                color: w.emph ? CRIMSON : active ? "#FFFFFF" : "#E6E1D8",
                opacity: shown ? 1 : 0,
                transform: `scale(${shown ? 0.96 + 0.04 * pop : 0.96})`,
                WebkitTextStroke: "4px #000",
                paintOrder: "stroke fill",
                textShadow: w.emph
                  ? "0 0 22px rgba(0,0,0,0.95), 0 0 34px rgba(228,33,63,0.55)"
                  : "0 6px 18px rgba(0,0,0,0.95)",
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Top context tag during the hook
const Tag: React.FC = () => {
  const f = useCurrentFrame();
  const o = interpolate(f, [6, 16, 130, 150], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ alignItems: "center", top: 250 }}>
      <div
        style={{
          fontFamily, fontWeight: 700, fontSize: 40, letterSpacing: 10, color: AMBER, opacity: o,
          textShadow: "0 3px 12px rgba(0,0,0,0.9)",
          borderTop: `2px solid ${CRIMSON}`, borderBottom: `2px solid ${CRIMSON}`, padding: "12px 28px",
        }}
      >
        ELAGABALUS · AD 218–222
      </div>
    </AbsoluteFill>
  );
};

const NextTag: React.FC = () => {
  const f = useCurrentFrame();
  const o = interpolate(f, [4, 14], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ alignItems: "center", top: 250 }}>
      <div
        style={{
          fontFamily, fontWeight: 700, fontSize: 40, letterSpacing: 10, color: AMBER, opacity: o,
          textShadow: "0 3px 12px rgba(0,0,0,0.9)",
          borderTop: `2px solid ${CRIMSON}`, borderBottom: `2px solid ${CRIMSON}`, padding: "12px 28px",
        }}
      >
        TOMORROW · CALIGULA
      </div>
    </AbsoluteFill>
  );
};

export const Short: React.FC = () => {
  const { fps } = useVideoConfig();
  useCinzel();
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {SHOTS.map((s, i) => {
        const from = Math.round(s.start * fps);
        const frames = Math.round(s.end * fps) - from;
        return (
          <Sequence key={i} from={from} durationInFrames={frames}>
            <Plate {...s} frames={frames} />
          </Sequence>
        );
      })}
      {FLASHES.map((t, i) => (
        <Sequence key={`f${i}`} from={Math.round(t * fps)} durationInFrames={6}>
          <Flash />
        </Sequence>
      ))}
      <Grain />
      <Tag />
      <Sequence from={Math.round(38.5 * fps)}>
        <NextTag />
      </Sequence>
      <Captions />
      <Audio src={staticFile("mix.wav")} />
    </AbsoluteFill>
  );
};
