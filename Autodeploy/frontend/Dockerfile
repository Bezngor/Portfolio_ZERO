FROM nginx:alpine

# Удаляем дефолтную конфигурацию nginx
RUN rm /etc/nginx/conf.d/default.conf

# Копируем нашу конфигурацию nginx
COPY nginx.conf /etc/nginx/conf.d/

# Копируем статические файлы
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/

# Открываем порт 80
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]

