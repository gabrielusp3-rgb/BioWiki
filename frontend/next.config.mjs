/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
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
