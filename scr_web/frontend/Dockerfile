FROM nginx:1.25-alpine

# Create directories with proper structure
RUN mkdir -p /usr/share/nginx/html/styles \
    /usr/share/nginx/html/scripts \
    /usr/share/nginx/html/assets \
    /var/log/nginx \
    /var/cache/nginx \
    && chmod -R 755 /var/log/nginx \
    && chmod -R 755 /var/cache/nginx

# Set working directory
WORKDIR /usr/share/nginx/html

# Copy HTML pages
COPY frontend/pages/index.html ./
COPY frontend/pages/404.html ./
COPY frontend/pages/50x.html ./
COPY frontend/pages/test.html ./test.html
COPY frontend/pages/refresh.html ./refresh.html

# Copy other HTML pages
COPY frontend/pages/login/login.html ./login.html
COPY frontend/pages/register/register.html ./register.html
COPY frontend/pages/chat/chat.html ./chat.html
COPY frontend/pages/tire/tire.html ./tire.html
COPY frontend/pages/maintenance/maintenance.html ./maintenance.html
COPY frontend/pages/verify-email/verify-email.html ./verify-email.html
COPY frontend/pages/admin/admin.html ./admin.html
COPY frontend/pages/auth-success/auth-success.html ./auth-success.html

# Copy static assets
COPY frontend/styles/ ./styles/
COPY frontend/scripts/ ./scripts/
COPY frontend/assets/ ./assets/

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost/health || exit 1

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
