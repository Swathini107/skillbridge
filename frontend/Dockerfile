# ==============================================================================
# SkillBridge Frontend Dockerfile
# Multi-stage production container for Vite React frontend
# ==============================================================================

FROM node:20-alpine as builder

WORKDIR /app

# Copy dependency specifications and install cleanly
COPY package*.json ./
RUN npm ci

# Copy application source code
COPY . .

# Accept optional build argument for VITE_API_URL
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

# Build production bundle
RUN npm run build


# Production stage with Nginx Alpine
FROM nginx:alpine

# Copy built static files to Nginx web root
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with SPA routing support
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
