# Реестр рекламных материалов — ЮгСтройИнвест

Статичный сайт-реестр материалов по ЖК Ростова-на-Дону. Один файл `index.html`, без сборки и зависимостей.

Имя проекта взято из логотипа: **ЮгСтройИнвест → `yugstroyinvest`**.

- Репозиторий: `yugstroyinvest-materials`
- Домен: `materials.yugstroyinvest.ru`

---

## Состав

| Файл | Назначение |
|---|---|
| `index.html` | весь сайт: разметка, стили, данные, логотип в base64 |
| `CNAME` | домен для GitHub Pages |
| `.nojekyll` | отключает обработку Jekyll |

---

## Вариант 1. GitHub Pages (бесплатно, рекомендуется)

### 1. Создать репозиторий
На github.com → **New repository** → имя `yugstroyinvest-materials` → **Public** → Create.

Приватный репозиторий тоже работает, но Pages из него доступны только на платных планах.

### 2. Залить файлы

Через веб-интерфейс: **Add file → Upload files** → перетащить `index.html`, `CNAME`, `.nojekyll` → **Commit changes**.

Через терминал:

```bash
cd путь/к/папке/site
git init
git add .
git commit -m "Реестр материалов"
git branch -M main
git remote add origin https://github.com/ВАШ_ЛОГИН/yugstroyinvest-materials.git
git push -u origin main
```

### 3. Включить Pages
**Settings → Pages** → Source: **Deploy from a branch** → Branch: `main`, папка `/ (root)` → **Save**.

Через 1–2 минуты сайт откроется по адресу
`https://ВАШ_ЛОГИН.github.io/yugstroyinvest-materials/`

### 4. Привязать домен

**В панели регистратора / DNS-хостинга** добавьте запись:

| Тип | Имя | Значение |
|---|---|---|
| CNAME | `materials` | `ВАШ_ЛОГИН.github.io` |

Если нужен корневой домен `yugstroyinvest.ru` — вместо CNAME четыре A-записи на `@`:
`185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`

**В GitHub:** Settings → Pages → Custom domain → `materials.yugstroyinvest.ru` → Save → дождаться зелёной галочки и включить **Enforce HTTPS**.

DNS обновляется от 10 минут до 24 часов.

---

## Вариант 2. Netlify (проще всего, без git)

1. Зайти на app.netlify.com → **Add new site → Deploy manually**.
2. Перетащить папку `site` в окно браузера. Сайт публикуется сразу.
3. **Site settings → Domain management → Add custom domain** → `materials.yugstroyinvest.ru`.
4. В DNS добавить CNAME `materials` → `имя-сайта.netlify.app`. HTTPS выпускается автоматически.

## Вариант 3. Свой хостинг

Загрузить `index.html` по FTP/SFTP в корень сайта (`public_html`, `www` или `/var/www/html`). Больше ничего не нужно — PHP, база и Node.js не требуются.

---

## Как обновлять содержимое

Все ссылки и даты лежат в массиве `DATA` внутри `index.html` (начало тега `<script>`).

```js
{ name:"47 кластер", url:"https://disk.yandex.ru/i/...", updated:"12.02.2026 10:30" },
```

- `name` — подпись строки
- `url` — ссылка (кнопка **Открыть**)
- `file` — имя PDF, если ссылки ещё нет (кнопка **PDF в таблице**)
- `updated` — метка `обновлено ДД.ММ.ГГГГ ЧЧ:ММ`; пустая строка даст «дата не указана»

Материалы моложе **45 дней** подсвечиваются автоматически.

После правки: сохранить файл → закоммитить в репозиторий (или перезалить на хостинг). На GitHub Pages изменения появляются через ~1 минуту.

---

## Ограничение доступа

Реестр публичный — по ссылке его увидит любой. Если материалы внутренние:

- **Netlify** — Site settings → Access control → пароль на весь сайт;
- **Cloudflare Access** — вход по корпоративной почте;
- либо разместить файл во внутренней сети компании.
