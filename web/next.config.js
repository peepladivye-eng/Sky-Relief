/** @type {import("next").NextConfig} */
const nextConfig = {
  // Allow maplibre-gl to be imported client-side only
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        "maplibre-gl": false,
      }
    }
    return config
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig