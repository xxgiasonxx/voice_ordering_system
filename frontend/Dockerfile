# 使用官方的 Node.js 映像檔作為建構階段
FROM node:22.14-alpine AS build

# 設定工作目錄
WORKDIR /app/frontend

# 複製 package.json 和 package-lock.json (如果有的話)
COPY package.json ./
# 如果您使用 yarn，則複製 yarn.lock
# COPY yarn.lock ./

# 安裝依賴項
RUN npm install

# 複製所有前端程式碼
COPY . .

# 建構前端應用程式
RUN npm run build

# 使用輕量的 Nginx 映像檔作為生產階段
FROM nginx:alpine

# 複製建構好的前端靜態檔案到 Nginx 的預設靜態檔案目錄
COPY --from=build /app/frontend/dist /usr/share/nginx/html

# 複製自定義的 Nginx 配置 (如果有的話，例如用於路由或 HTTPS)
# 如果您有自定義的 Nginx 配置，請在前端專案根目錄創建一個 `nginx.conf` 檔案
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 Nginx 服務的埠口
EXPOSE 80

# 啟動 Nginx 服務
CMD ["nginx", "-g", "daemon off;"]