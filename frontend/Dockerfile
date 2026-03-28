# === Stage 1: Frontend 빌드 (React + Vite) ===
FROM node:20-alpine AS builder

WORKDIR /app

# 패키지 파일 복사
COPY frontend/package*.json ./

# 의존성 설치
RUN npm ci

# 소스 복사
COPY frontend/ .

# Build-time 환경변수 (Google OAuth)
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

# 빌드
RUN npm run build

# === Stage 2: Production (Nginx) ===
FROM nginx:alpine

# nginx 설정 복사
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Frontend 빌드 결과물 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# 포트 노출
EXPOSE 4040

CMD ["nginx", "-g", "daemon off;"]
