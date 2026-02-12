# Frontend Dockerfile - Next.js with hot reload
#
# Development image optimized for:
# - Fast rebuilds
# - Hot reload via Next.js dev server
# - Source mounted as volume

FROM node:22-alpine

# Set working directory
WORKDIR /app

# Install dependencies first for layer caching
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy application code
# Note: In development, src/ and public/ are overridden by volume mounts
COPY . .

# Expose port
EXPOSE 3000

# Set environment for development
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Default command
CMD ["npm", "run", "dev"]
