# syntax=docker/dockerfile:1.6
FROM node:20 AS build
WORKDIR /app
COPY frontend/package.json package.json
COPY frontend/admin/package.json admin/package.json
COPY frontend/pwa/package.json pwa/package.json
COPY frontend/tv/package.json tv/package.json
## Faster, reproducible installs with cache mount
RUN --mount=type=cache,target=/root/.npm npm install --no-audit --prefer-offline
COPY frontend ./
RUN npm run build --workspace pwa

FROM nginx:1.25-alpine
COPY --from=build /app/pwa/dist /usr/share/nginx/html
COPY frontend/pwa/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
