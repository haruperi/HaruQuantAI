/** @type {import('next').NextConfig} */

// The frontend calls the FastAPI gateway same-origin via a dev rewrite so that
// session (hq_session) and CSRF (hq_csrf) cookies stay first-party and CORS is
// avoided. BACKEND_URL may be overridden in the local environment.
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig = {
  reactStrictMode: true,
  // Backtest-scale bar reads are genuinely slow at the broker: a million M1
  // bars takes MT5 about three minutes to return. The rewrite proxy's 30s
  // default aborts those with a 500 that looks like a gateway fault, so it is
  // raised past the slowest read the Chart widget can ask for.
  experimental: {
    proxyTimeout: 600_000,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
