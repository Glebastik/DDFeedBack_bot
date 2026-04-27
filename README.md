# DDFeetBackBot — Telegram-бот отзывов для сети кофеен

## Структура проекта

```
project/
  bot/
    __init__.py
    main.py
    config.py
    keyboards.py
    states.py
    handlers.py
    google_sheets.py
  .env.example
  requirements.txt
  README.md
```

---

## Настройка

### 1. Создайте файл `.env`

Скопируйте `.env.example` и заполните значения:

```bash
cp .env.example .env
```

Содержимое `.env`:

```env
BOT_TOKEN=your_telegram_bot_token_here
GOOGLE_APPS_SCRIPT_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
DISCOUNT_REDIRECT_URL=https://example.com/discount
```

- `BOT_TOKEN` — токен бота от [@BotFather](https://t.me/BotFather)
- `GOOGLE_APPS_SCRIPT_URL` — URL задеплоенного Google Apps Script Web App
- `DISCOUNT_REDIRECT_URL` — ссылка на страницу со скидкой

---

### 2. Установите зависимости

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

### 3. Запустите бота

```bash
python -m bot.main
```

---

## Примеры JSON, отправляемых в Apps Script

### Гневный отзыв

```json
{
  "type": "angry_review",
  "text": "Кофе был холодным!",
  "username": "ivan_petrov",
  "user_id": 123456789,
  "full_name": "Иван Петров",
  "created_at": "2024-04-27 15:30:00"
}
```

### Позитивный отзыв

```json
{
  "type": "positive_review",
  "text": "Лучший раф в городе!",
  "username": "anna_k",
  "user_id": 987654321,
  "full_name": "Анна К.",
  "created_at": "2024-04-27 16:00:00"
}
```

### Валентинка для бариста

```json
{
  "type": "valentine",
  "barista_name": "Маша",
  "cafe_address": "ул. Ленина, 10",
  "text": "Спасибо за улыбку и вкусный кофе!",
  "username": "sergey_m",
  "user_id": 111222333,
  "full_name": "Сергей М.",
  "created_at": "2024-04-27 17:15:00"
}
```

---

## Google Apps Script

Создайте новый проект на [script.google.com](https://script.google.com), вставьте код ниже и опубликуйте как **Web App** (Execute as: Me, Who has access: Anyone).

Замените `YOUR_SPREADSHEET_ID` на ID вашей Google Таблицы (из URL).

В таблице должны быть три листа: **Гневные отзывы**, **Позитивные отзывы**, **Валентинки**.

```javascript
var SPREADSHEET_ID = "YOUR_SPREADSHEET_ID";

// Заголовки для каждого типа листа
var HEADERS = {
  "Гневные отзывы":    ["Дата/время", "Тип",  "Текст отзыва", "Username", "User ID", "Имя"],
  "Позитивные отзывы": ["Дата/время", "Тип",  "Текст отзыва", "Username", "User ID", "Имя"],
  "Валентинки":        ["Дата/время", "Тип",  "Кому",         "Адрес кофейни", "Текст", "Username", "User ID", "Имя"]
};

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var ss   = SpreadsheetApp.openById(SPREADSHEET_ID);

    // Определяем лист по полю sheet_name, присланному ботом
    var sheetName = data.sheet_name || "Гневные отзывы";
    var sheet     = ss.getSheetByName(sheetName);

    if (!sheet) {
      throw new Error("Лист не найден: " + sheetName);
    }

    // Добавляем заголовки, если лист пустой
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(HEADERS[sheetName]);
      sheet.getRange(1, 1, 1, HEADERS[sheetName].length)
           .setFontWeight("bold");
    }

    var row = [];

    if (data.type === "angry_review" || data.type === "positive_review") {
      row = [
        data.created_at  || new Date(),
        data.type        || "",
        data.text        || "",
        data.username    || "",
        data.user_id     || "",
        data.full_name   || ""
      ];

    } else if (data.type === "valentine") {
      row = [
        data.created_at    || new Date(),
        data.type          || "",
        data.barista_name  || "",
        data.cafe_address  || "",
        data.text          || "",
        data.username      || "",
        data.user_id       || "",
        data.full_name     || ""
      ];

    } else {
      throw new Error("Неизвестный тип: " + data.type);
    }

    sheet.appendRow(row);

    return ContentService
      .createTextOutput(JSON.stringify({ status: "ok" }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    Logger.log("doPost error: " + err.message);
    return ContentService
      .createTextOutput(JSON.stringify({ status: "error", message: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
```

---

## Docker

### Сборка и запуск вручную

```bash
docker build -t ddfeetbackbot .

docker run -d \
  --name ddfeetbackbot \
  --restart always \
  --env-file .env \
  ddfeetbackbot
```

> `.env` передаётся через `--env-file`, файл **не копируется** в образ (он в `.dockerignore`).

---

## CI/CD (GitHub Actions)

Пайплайн находится в `.github/workflows/ci-cd.yml`.  
Запускается при каждом пуше в ветку `master`.

### Шаги

1. **build-and-push** — собирает Docker-образ и пушит два тега на Docker Hub: `latest` и короткий хэш коммита.
2. Watchtower на сервере автоматически подхватывает новый `latest`-образ и перезапускает контейнер.

### Необходимые секреты в GitHub (Settings → Secrets → Actions)

| Секрет            | Значение                         |
|-------------------|----------------------------------|
| `DOCKER_USERNAME` | Логин на Docker Hub              |
| `DOCKER_PASSWORD` | Пароль / Access Token Docker Hub |

---

## Команды бота

| Команда   | Действие                        |
|-----------|---------------------------------|
| `/start`  | Показать главное меню           |
| `/cancel` | Отменить текущий сценарий       |


By Gleb