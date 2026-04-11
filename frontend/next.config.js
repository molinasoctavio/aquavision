/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'http',  hostname: 'localhost'                       },
      { protocol: 'https', hostname: '*.up.railway.app'                },
      { protocol: 'https', hostname: '*.vercel.app'                    },
      { protocol: 'https', hostname: 'cdn.aquavision.io'               },
    ],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

module.exports = nextConfig;
