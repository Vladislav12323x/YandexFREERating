# CloudShare

Хранилище файлов

## Установка 
Создание папки для базы данных
```bash
mkdir instance
```
Установка зависимостей
```bash
pip install -r requirements.txt
```
Запуск
```bash
gunicorn app:create_app()
```
