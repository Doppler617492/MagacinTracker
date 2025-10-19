FROM node:20 AS build

# Accept build arguments
ARG VITE_TV_DEVICE_ID
ARG VITE_TV_DEVICE_SECRET
ARG VITE_API_URL

# Set environment variables for the build
ENV VITE_TV_DEVICE_ID=$VITE_TV_DEVICE_ID
ENV VITE_TV_DEVICE_SECRET=$VITE_TV_DEVICE_SECRET
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /app
COPY frontend/package.json package.json
COPY frontend/admin/package.json admin/package.json
COPY frontend/pwa/package.json pwa/package.json
COPY frontend/tv/package.json tv/package.json
RUN npm install
COPY frontend ./
RUN npm run build --workspace tv

FROM nginx:1.25-alpine
COPY --from=build /app/tv/dist /usr/share/nginx/html
COPY frontend/tv/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
