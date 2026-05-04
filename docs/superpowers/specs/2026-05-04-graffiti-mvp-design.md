# MVP Дизайн: Карта графіті

**Дата:** 2026-05-04  
**Статус:** Затвердженo  
**Автор:** Brainstorming Session

---

## 1. Огляд проекту

Мобільний додаток для картування графіті з функціями:
- Перегляду локацій на карті (публічно)
- Створення нових локацій (з аутентифікацією)
- Завантаження фотографій (S3)
- Голосування: "існує" / "не існує"
- Пошуку в радіусі 1-5 км (PostGIS)

**Тривалість:** 2-3 тижні MVP розробки

---

## 2. Архітектура

### 2.1 Компоненти системи

```
┌─────────────────┐
│   Мобільний app │
└────────┬────────┘
         │ REST API (HTTP/JSON)
         ▼
┌─────────────────────────────────┐
│   Django REST API               │
├─────────────────────────────────┤
│ • apps/authentication (JWT)     │
│ • apps/users (користувачі)      │
│ • apps/graffiti (НОВА)          │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   PostgreSQL + PostGIS          │
│ (геопросторові запити)          │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   AWS S3 (сховище фотографій)   │
└─────────────────────────────────┘
```

### 2.2 Структура новой app `graffiti`

```
apps/graffiti/
├── models.py           # Graffiti, Photo, Vote, Location
├── serializers.py      # GraffitiSerializer, PhotoSerializer, VoteSerializer
├── views.py            # GraffitiViewSet, PhotoViewSet, VoteViewSet
├── filters.py          # GeometryFilter для радіусного пошуку
├── permissions.py      # IsOwnerOrReadOnly
├── urls.py             # Маршрути
├── apps.py
├── admin.py
├── migrations/
└── tests/              # (користувач писатиме тести самостійно)
```

---

## 3. Дата-моделі

### 3.1 Graffiti

```python
class Graffiti(models.Model):
    id              = UUIDField(primary_key=True, default=uuid4)
    title           = CharField(max_length=255)
    description     = TextField()
    author          = ForeignKey(User, on_delete=CASCADE)
    location        = PointField()  # PostGIS: (lat, lon)
    created_at      = DateTimeField(auto_now_add=True)
    updated_at      = DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            GistIndex(fields=['location']),  # PostGIS індекс для швидкого пошуку
        ]
```

### 3.2 Photo

```python
class Photo(models.Model):
    id              = UUIDField(primary_key=True, default=uuid4)
    graffiti        = ForeignKey(Graffiti, on_delete=CASCADE, related_name='photos')
    image           = ImageField(storage=s3_storage, upload_to='graffiti_photos/')
    uploaded_at     = DateTimeField(auto_now_add=True)
```

### 3.3 Vote

```python
class Vote(models.Model):
    VOTE_CHOICES = [
        ('exists', 'Існує'),
        ('not_exists', 'Не існує'),
    ]
    
    id              = UUIDField(primary_key=True, default=uuid4)
    graffiti        = ForeignKey(Graffiti, on_delete=CASCADE, related_name='votes')
    user            = ForeignKey(User, on_delete=CASCADE)
    vote_type       = CharField(max_length=20, choices=VOTE_CHOICES)
    created_at      = DateTimeField(auto_now_add=True)
    updated_at      = DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('graffiti', 'user')  # один голос на користувача
```

---

## 4. REST API

### 4.1 Публічні endpoints (AllowAny)

```
GET    /api/graffiti/
       Список всіх графіті (паджинація, page-based)
       Query params: page=1&page_size=20
       
GET    /api/graffiti/{id}/
       Деталі однієї локації (з кількістю голосів)
       
GET    /api/graffiti/search/radius/
       Пошук у радіусі
       Query params: lat=50.45&lon=30.52&radius=5
       radius у км, результати сортовані по дистанції
```

### 4.2 Аутентифіковані endpoints (IsAuthenticated)

```
POST   /api/graffiti/
       Створити нову графіті-локацію
       Body: { title, description, latitude, longitude, photos[] }
       
PATCH  /api/graffiti/{id}/
       Редагувати (тільки автор)
       
DELETE /api/graffiti/{id}/
       Видалити (тільки автор)
       
POST   /api/graffiti/{id}/photos/
       Завантажити фото (тільки автор)
       
DELETE /api/graffiti/{id}/photos/{photo_id}/
       Видалити фото (тільки автор)
       
POST   /api/graffiti/{id}/votes/
       Створити або оновити голос (один на користувача)
       Body: { vote_type: 'exists' | 'not_exists' }
       
GET    /api/graffiti/{id}/votes/
       Статистика голосів
       Response: { exists_count, not_exists_count }
```

---

## 5. Аутентифікація та дозволи

### 5.1 JWT (вже налаштовано)

- `POST /api/auth/token/` — отримати токен (username + password)
- `POST /api/auth/token/refresh/` — оновити токен
- Всі приватні запити: `Authorization: Bearer <token>`

### 5.2 Permission classes

```python
# GraffitiViewSet
list()     → AllowAny
retrieve() → AllowAny
create()   → IsAuthenticated
update()   → IsAuthenticated + IsOwnerOrReadOnly
destroy()  → IsAuthenticated + IsOwnerOrReadOnly

# PhotoViewSet
create()   → IsAuthenticated + IsOwnerOrReadOnly
destroy()  → IsAuthenticated + IsOwnerOrReadOnly

# VoteViewSet
create()   → IsAuthenticated
update()   → IsAuthenticated (юзер голосує за себе)
```

**Кастомний permission:** `IsOwnerOrReadOnly`
- Дозволяє редагування/видалення тільки власнику об'єкту
- Читання дозволено всім

---

## 6. Завантаження фотографій (S3)

### 6.1 Налаштування

- **Пакет:** `django-storages[s3]` + `boto3`
- **Credentials:** AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (з .env)
- **Bucket:** `graffiti-mvp-bucket` (або назва, яку ви виберете)
- **Public access:** S3 об'єкти публічні (URL для читання)

### 6.2 Процес

1. Клієнт POST `/api/graffiti/{id}/photos/` + файл
2. Django автоматично загружає на S3 через django-storages
3. API повертає URL фото (публічний S3 link)
4. Мобільний app отримує URL і показує зображення

### 6.3 Валідація

- **Типи:** JPEG, PNG тільки
- **Розмір:** max 5MB
- **Масштабування:** не робимо (MVP)

---

## 7. Геолокаційний пошук (PostGIS)

### 7.1 Радіусний пошук

```sql
SELECT * FROM graffiti_graffiti
WHERE ST_DWithin(
  location,
  ST_MakePoint(lon, lat),
  radius_meters
)
ORDER BY ST_Distance(location, ST_MakePoint(lon, lat)) ASC
```

### 7.2 API query

```
GET /api/graffiti/search/radius/?lat=50.45&lon=30.52&radius=5
```

Параметри:
- `lat`, `lon` — координати центру
- `radius` — радіус у км

Результат: список графіті, відсортований по дистанції, з полем `distance_km` в JSON.

### 7.3 Додаткові фільтри (опціонально)

```
?author={user_id}     # Фільтр по автору
?created_after=DATE   # По даті створення
```

---

## 8. Обробка помилок

### 8.1 HTTP статус коди

```
200 OK           — успішний запит
201 Created      — об'єкт створений
204 No Content   — видалено успішно
400 Bad Request  — неправильні дані
403 Forbidden    — немає дозволу (не власник)
404 Not Found    — об'єкт не знайдено
500 Server Error — внутрішня помилка
```

### 8.2 Формат помилок

```json
{
  "detail": "Ви не маєте дозволу редагувати цей об'єкт"
}
```

При валідаційних помилках:

```json
{
  "title": ["Це поле обов'язкове"],
  "description": ["Мінімум 10 символів"]
}
```

### 8.3 S3 помилки

- Якщо завантаження на S3 не вдалось → 400 Bad Request з описом
- Якщо фото завелике → 400 Bad Request

---

## 9. Паджинація

**Тип:** Page-based (стандартна DRF паджинація)

```
GET /api/graffiti/?page=1&page_size=20
```

Відповідь:

```json
{
  "count": 150,
  "next": "http://api.example.com/graffiti/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## 10. Статистика голосів

На кожній графіті показуємо:

```json
{
  "id": "uuid",
  "title": "...",
  "votes": {
    "exists": 5,
    "not_exists": 2
  }
}
```

Юзер може:
- Створити голос: `POST /api/graffiti/{id}/votes/`
- Оновити голос: `PATCH /api/graffiti/{id}/votes/` (змінити його вибір)
- Один голос на користувача (unique constraint)

---

## 11. Поточний стан проекту

**Вже готово:**
- ✅ Django + DRF налаштовано
- ✅ PostgreSQL налаштовано
- ✅ JWT аутентифікація (apps/authentication)
- ✅ Custom User модель (apps/users)
- ✅ Базова структура проекту

**Потрібно реалізувати:**
- ❌ PostgreSQL + PostGIS в settings
- ❌ App `graffiti` з моделями
- ❌ Serializers для Graffiti, Photo, Vote
- ❌ ViewSets + endpoints
- ❌ Permission IsOwnerOrReadOnly
- ❌ Геофільтр для radius search
- ❌ Налаштування django-storages + S3
- ❌ API документація (опціонально: Swagger)

---

## 12. План реалізації (2-3 тижні)

### День 1-2: Налаштування
- Включити PostGIS в settings
- Встановити django-storages[s3]
- Налаштувати S3 credentials

### День 3-4: Моделі та serializers
- Написати Graffiti, Photo, Vote моделі
- Написати serializers
- Тести для моделей (користувач)

### День 5-7: API endpoints
- Написати ViewSets
- Реалізувати CRUD
- Дозволи IsOwnerOrReadOnly

### День 8-9: Геопошук
- Реалізувати radius search
- Сортування по дистанції
- Тести для запитів (користувач)

### День 10-11: Голосування
- Реалізувати Vote model API
- Обновлення голосу (один на користувача)
- Статистика голосів

### День 12-13: Фотографії
- S3 інтеграція
- Upload/delete endpoints
- Валідація файлів

### День 14-21: Полірування
- API документація (Swagger)
- Demo dataset
- Тестування (користувач)
- Баг-фікси

---

## 13. Ключові рішення дизайну

| Питання | Рішення | Причина |
|---------|---------|---------|
| Геолокація | PostGIS | Точні spatial queries для radius search |
| Сховище | AWS S3 | Масштабованість, простота S3 API |
| Архітектура | Монолітна app | Швидко реалізувати MVP, чистий код |
| Голосування | Один голос, можна оновити | User-friendly, простіше в реалізації |
| Дозволи | IsOwnerOrReadOnly | Захист від вандалізму, публічне читання |
| Паджинація | Page-based | Стандартно в DRF, простіше за cursor |
| Фото | Без масштабування | Скоротити scope для MVP |

---

## 14. Що НЕ робимо (поза MVP scope)

- ❌ WebSockets / real-time updates
- ❌ Модерація / approval workflow
- ❌ Advanced analytics
- ❌ Elasticsearch
- ❌ Кешування (Redis)
- ❌ Rate limiting
- ❌ Множинні мови
- ❌ Mobile app (тільки API)

---

## Затвердження

- ✅ Архітектура затверджена
- ✅ Моделі затверджені
- ✅ API endpoints затверджені
- ✅ Дизайн готовий до реалізації