FROM node:14

# Создать директорию приложения
WORKDIR /app

# Установить зависимости
COPY package*.json ./
RUN npm install

# Скопировать исходный код
COPY . .

# Запустить приложение
CMD ["node", "app.js"]
