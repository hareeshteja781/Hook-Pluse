FROM node:24-alpine AS build
ARG VITE_ENABLE_TEST_LOGIN=false
ENV VITE_ENABLE_TEST_LOGIN=$VITE_ENABLE_TEST_LOGIN
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
