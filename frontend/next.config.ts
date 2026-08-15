import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  turbopack: {
    rules: {
      '**/*.geojson': {
        loaders: ['json-loader'],
        as: '*.json',
      },
    },
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'picsum.photos',
        port: '',
        pathname: '/**',
      },
    ],
  },
  webpack: (config) => {
    config.module.rules.push({
      test: /\.geojson$/,
      use: ['json-loader'],
    });
    return config;
  },
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    return [
      { source: '/api/floats', destination: `${backendUrl}/api/floats` },
      { source: '/api/refresh-floats', destination: `${backendUrl}/api/refresh-floats` },
      { source: '/api/float/:path*', destination: `${backendUrl}/api/float/:path*` },
      { source: '/query', destination: `${backendUrl}/query` },
      { source: '/session/:path*', destination: `${backendUrl}/session/:path*` },
      { source: '/api/graph/:path*', destination: `${backendUrl}/api/graph/:path*` },
      { source: '/graph/:path*', destination: `${backendUrl}/graph/:path*` },
    ];
  },
};

export default nextConfig;
