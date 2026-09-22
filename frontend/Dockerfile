FROM node:20-alpine AS build
WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY . .
# Vite env vars are baked in at build time, not read at container start.
ARG VITE_ADMIN_KEY
ENV VITE_ADMIN_KEY=$VITE_ADMIN_KEY
RUN pnpm build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
