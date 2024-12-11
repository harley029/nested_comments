# Django Blog with Nested Comments

## Описание

Это проект блога на Django с возможностью публикации постов и оставления вложенных комментариев, с добавлением текстовых и графических файлов к ним. Интерфейс позволяет производить сортировку сообщений по дате, имени пользователя или адресу электронной почты. Во время создания комментария присутствует предварительный просмотр, что позволяет не перегружать страницу и сразу видеть результат. Кроме того, в наличии ппанель с кнопками самых распространенных тегов, что упрощает ввод текста в формате "маркдаун". 
Зарегистрированные пользователи могут создавать как новые посты так и комментраии, в то время как незарегистрированные только комментарии. При этом, форма ввода данных автоматически подстраивается под различных видов пользователей, показывая для заполнения разные наборы полей (зарегистрированным пользователям не нужно будет вводить свои имя и адрес электронной почты).
База банных реализована на PostgreSQL и хранит данные о всех постах, комментариях к ним и пользователях, что позволяет в случае необходимости идентифецировать конкретного поьзователя.

## Установка

### Вариант с запущеным сервером PostgreSQL
1. Клонируйте репозиторий
2. Установите зависимости:
    pip install -r requirements.txt
3. Заполните переменные окружения в файле .env
4. Выполните миграции:
    python manage.py migrate
5. Создайте администратора:
    python manage.py createsuperuser
6. Запустите сервер разработки:
    python manage.py runserver

### Вариант с использованием Docker
1. Клонируйте репозиторий
2. Запустите Docker
3. Заполните переменные окружения в файле .env
4. Создайте образ и запустите контейнер:
    docker compose up --build -d
5. Выполните миграции:
    docker compose exec web python manage.py migrate
6. Создайте администратора:
    docker-compose exec web python manage.py createsuperuser

### Вариант с использованием готового и настроенного образа Docker Hub
1. Клонируйте и запустите контейнер:
    docker pull harley029/nested_comments
    docker run -p 8000:8000 --name nested_comments harley029/nested_comments

## Использование

Перейдите по адресу `http://localhost:8000/` для просмотра блога.

## Требования

- Python 3.12+
- Django 5.0+
- PostgreSQL 13+

## Дополнительные сведения

В папке Docker находятся файли Docker, env для самостоятельной сборки и запуска образов проекта через Docker compose или Docker Hub. 