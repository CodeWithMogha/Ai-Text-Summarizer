/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for catching bugs early
  reactStrictMode: true,

  // Configure environment variables that are safe to expose to the browser
  // Variables starting with NEXT_PUBLIC_ are automatically exposed
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // Production optimizations
  // Disable x-powered-by header (minor security improvement)
  poweredByHeader: false,

  // Configure allowed image domains if needed
  images: {
    domains: [],
  },
};

module.exports = nextConfig;
