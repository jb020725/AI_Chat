# Build stage
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built frontend files from builder stage
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port (Cloud Run expects 8080)
EXPOSE 8080

# Start nginx on port 8080
CMD ["nginx", "-g", "daemon off;"]
