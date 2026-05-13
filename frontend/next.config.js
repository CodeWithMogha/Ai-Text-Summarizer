const repo = 'Ai-Text-Summarizer';

const nextConfig = {
  // Enable static export for GitHub Pages
  output: 'export',
  
  // Set the base path for GitHub Pages subpath deployment
  basePath: `/${repo}`,
  assetPrefix: `/${repo}/`,

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },

  reactStrictMode: true,

  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  poweredByHeader: false,
};

module.exports = nextConfig;
