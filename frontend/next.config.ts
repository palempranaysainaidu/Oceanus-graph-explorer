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
    const mapsBackendUrl = process.env.NEXT_PUBLIC_MAPS_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const chatbotBackendUrl = process.env.NEXT_PUBLIC_CHATBOT_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';

    return [
      { source: '/api/floats', destination: `${mapsBackendUrl}/api/floats` },
      { source: '/api/refresh-floats', destination: `${mapsBackendUrl}/api/refresh-floats` },
      { source: '/api/float/:path*', destination: `${mapsBackendUrl}/api/float/:path*` },
      { source: '/api/graph/:path*', destination: `${mapsBackendUrl}/api/graph/:path*` },
      { source: '/graph/:path*', destination: `${mapsBackendUrl}/graph/:path*` },
      { source: '/query', destination: `${chatbotBackendUrl}/query` },
      { source: '/session/:path*', destination: `${chatbotBackendUrl}/session/:path*` },
    ];
  },
};

export default nextConfig;
