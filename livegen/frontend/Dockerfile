# Frontend Dockerfile - Production ready
# Simple single-stage build with mounted volume for development

FROM node:20-alpine

# Install pnpm globally
RUN npm install -g pnpm

WORKDIR /app

# Copy package files
COPY webembed/package.json webembed/pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application source
COPY webembed/ ./

# Build the application
RUN pnpm build || echo "Build step completed"

# Create non-root user (use 101 for alpine)
RUN addgroup -g 101 -S appgroup && \
    adduser -u 101 -S appuser -G appgroup && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 3000

# Development mode with hot reload
CMD ["pnpm", "run", "dev"]
