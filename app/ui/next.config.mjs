/** @type {import('next').NextConfig} */

// The frontend calls the FastAPI gateway same-origin via a dev rewrite so that
// session (hq_session) and CSRF (hq_csrf) cookies stay first-party and CORS is
// avoided. BACKEND_URL may be overridden in the local environment.
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig = {
  reactStrictMode: true,
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
