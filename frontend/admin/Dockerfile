FROM node:20 AS build
WORKDIR /app
COPY frontend/package.json package.json
COPY frontend/admin/package.json admin/package.json
COPY frontend/pwa/package.json pwa/package.json
COPY frontend/tv/package.json tv/package.json
RUN npm install
COPY frontend ./
RUN npm run build --workspace admin

FROM nginx:1.25-alpine
COPY --from=build /app/admin/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
