FROM nginx:alpine

# Copy built frontend files
COPY dist/ /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port (Cloud Run expects 8000)
EXPOSE 8000

# Start nginx on port 8000
CMD ["nginx", "-g", "daemon off;"]
