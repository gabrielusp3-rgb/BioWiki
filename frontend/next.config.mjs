function cspConnectSrc() {
  const origins = new Set(["'self'", "https://biowiki-api.vercel.app"]);
  for (const raw of [process.env.NEXT_PUBLIC_API_URL, process.env.NEXT_PUBLIC_SITE_URL]) {
    if (!raw) continue;
    try {
      origins.add(new URL(raw).origin);
    } catch {
      /* ignore malformed env */
    }
  }
  if (process.env.NODE_ENV !== "production") {
    origins.add("http://127.0.0.1:8000");
    origins.add("http://localhost:8000");
  }
  return [...origins].join(" ");
}

/** Production CSP compatible with Next.js hydration, next/font, Three.js, and splash video. */
function contentSecurityPolicy() {
  const scriptSrc =
    process.env.NODE_ENV === "production"
      ? "script-src 'self' 'unsafe-inline'"
      : "script-src 'self' 'unsafe-inline' 'unsafe-eval'";
  return [
    "default-src 'self'",
    scriptSrc,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    `connect-src ${cspConnectSrc()}`,
    "media-src 'self' blob:",
    "worker-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
    "form-action 'self'",
  ].join("; ");
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  async redirects() {
    return [
      {
        source: "/api",
        destination: "https://biowiki-api.vercel.app/docs",
        permanent: false,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          { key: "Content-Security-Policy", value: contentSecurityPolicy() },
        ],
      },
    ];
  },
  transpilePackages: [
    "three",
    "@react-three/fiber",
    "@react-three/drei",
    "@react-three/postprocessing",
  ],
  experimental: {
    optimizePackageImports: ["framer-motion"],
  },
};

// Standalone output is for the Docker image. Vercel ignores a custom distDir
// layout and should not use `output: "standalone"`.
if (!process.env.VERCEL) {
  nextConfig.output = "standalone";
}

export default nextConfig;
