# frontend/neith/Dockerfile
# NEITH -- Network Entity Intelligence & Threat Hunter
# Frontend container image (Next.js).
#
# Multi-stage build:
#   Stage 1 (builder): install dependencies and produce the production build.
#   Stage 2 (runner):  copy only the standalone output into a minimal image.
#
# Build:  docker build -t neith-frontend -f frontend/neith/Dockerfile .
# Run:    docker run -p 3000:3000 neith-frontend

FROM node:18-alpine AS builder

WORKDIR /app

# -- Install dependencies ---------------------------------------
COPY frontend/neith/package.json frontend/neith/package-lock.json ./
RUN npm ci

# -- Copy source and build --------------------------------------
COPY frontend/neith/ ./

# Next.js standalone output minimises the runner image size
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# -- Runner stage -----------------------------------------------
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Non-root user for security
RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 nextjs

# Copy standalone output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
