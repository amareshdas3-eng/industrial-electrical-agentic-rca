/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: '/industrial-electrical-agentic-rca',
  images: { unoptimized: true },
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },
};

module.exports = nextConfig;
