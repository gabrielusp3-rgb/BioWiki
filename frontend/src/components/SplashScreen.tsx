"use client";

import { useEffect, useRef, useState } from "react";

/**
 * BIOWIKI cinematic splash screen.
 *
 * Non-invasive overlay: the application mounts and initialises normally
 * underneath (providers, services, API clients, assets); this component only
 * paints a fixed full-screen layer on top and removes itself once BOTH the
 * intro video has finished AND the app has finished loading.
 *
 * To use a different intro clip in the future, simply replace
 * `frontend/public/splash.mp4` (and optionally `splash-poster.jpg`) — no logic
 * changes are required.
 */

// Media lives in /public so it can be swapped without touching this file.
const VIDEO_SRC = "/splash.mp4";
// Fade-out duration (ms). Kept inside the 400–800 ms window from the brief.
const FADE_MS = 600;
// Safety net only: prevents an indefinite splash if `window.load` never fires
// (e.g. a stalled resource). It does NOT drive the normal timing, which is
// governed by the two real events (video ended + app loaded).
const APP_READY_SAFETY_MS = 12000;

export function SplashScreen() {
  // Overlay present in the DOM. Starts true so there is no initial flash.
  const [mounted, setMounted] = useState(true);
  // Drives the opacity transition before unmount.
  const [fading, setFading] = useState(false);
  // The two real completion signals we synchronise on.
  const [videoDone, setVideoDone] = useState(false);
  const [appReady, setAppReady] = useState(false);
  // Decided on the client after mount so SSR HTML matches the first paint.
  const [clientReady, setClientReady] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    setClientReady(true);
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (query.matches) {
      setReducedMotion(true);
      setVideoDone(true);
    }
  }, []);

  useEffect(() => {
    if (fading) {
      delete document.documentElement.dataset.biowikiSplash;
      window.dispatchEvent(new Event("biowiki-splash-end"));
      return;
    }
    document.documentElement.dataset.biowikiSplash = "1";
    window.dispatchEvent(new Event("biowiki-splash-start"));
    return () => {
      delete document.documentElement.dataset.biowikiSplash;
      window.dispatchEvent(new Event("biowiki-splash-end"));
    };
  }, [fading]);

  // "App loaded" signal — silent and non-blocking. `window.load` fires after
  // the document and its assets are ready; a safety timer backs it up.
  useEffect(() => {
    if (document.readyState === "complete") {
      setAppReady(true);
      return;
    }
    const onLoad = () => setAppReady(true);
    window.addEventListener("load", onLoad, { once: true });
    const safety = window.setTimeout(() => setAppReady(true), APP_READY_SAFETY_MS);
    return () => {
      window.removeEventListener("load", onLoad);
      window.clearTimeout(safety);
    };
  }, []);

  // Kick off playback; if autoplay is blocked or the clip errors, don't hang.
  useEffect(() => {
    if (reducedMotion) return;
    const video = videoRef.current;
    if (!video) return;
    const attempt = video.play?.();
    if (attempt && typeof attempt.catch === "function") {
      attempt.catch(() => setVideoDone(true));
    }
  }, [reducedMotion]);

  // Remove the splash only when BOTH real conditions are satisfied.
  useEffect(() => {
    if (!videoDone || !appReady || fading) return;
    setFading(true);
    const timer = window.setTimeout(() => {
      setMounted(false);
      // Release the decoded video from memory after the overlay is gone.
      const video = videoRef.current;
      if (video) {
        try {
          video.pause();
          video.removeAttribute("src");
          video.load();
        } catch {
          /* element already detached — nothing to release */
        }
      }
    }, FADE_MS);
    return () => window.clearTimeout(timer);
  }, [videoDone, appReady, fading]);

  if (!mounted) return null;

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-black"
      style={{
        opacity: fading ? 0 : 1,
        transition: `opacity ${FADE_MS}ms ease-in-out`,
        pointerEvents: fading ? "none" : "auto",
      }}
    >
      {!clientReady ? null : reducedMotion ? (
        <div className="flex flex-col items-center gap-3">
          <span className="font-display text-4xl font-bold uppercase tracking-tightest text-white sm:text-5xl">
            BIOWIKI
          </span>
          <span className="font-display text-[11px] uppercase tracking-[0.3em] text-white/50">
            Sequence Database
          </span>
        </div>
      ) : (
        <video
          ref={videoRef}
          className="h-full w-full object-contain"
          src={VIDEO_SRC}
          autoPlay
          muted
          playsInline
          preload="auto"
          controls={false}
          onEnded={() => setVideoDone(true)}
          onError={() => setVideoDone(true)}
        />
      )}

      {videoDone && !appReady && (
        <span className="absolute bottom-10 left-1/2 -translate-x-1/2 font-display text-[11px] uppercase tracking-[0.25em] text-white/60">
          Finalizando carregamento…
        </span>
      )}
    </div>
  );
}
