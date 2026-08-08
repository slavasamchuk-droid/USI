"""
Функция-посредник между админкой и GitHub.

Токен GitHub хранится в переменных окружения функции и никогда не попадает в браузер.
Сотрудник вводит только пароль отдела — аккаунт GitHub ему не нужен.

Переменные окружения (задаются при создании функции):
  GH_TOKEN   — токен GitHub с правом записи (contents: read and write)
  GH_OWNER   — владелец репозитория, например slavasamchuk-droid
  GH_REPO    — репозиторий, например USIlinks
  GH_BRANCH  — ветка, обычно main
  GH_PATH    — путь к файлу данных, обычно data.json
  APP_PASS   — пароль отдела, который вводят сотрудники в админке
  ALLOW_ORIGIN — адрес админки, например https://slavasamchuk-droid.github.io
                 (можно поставить *, но лучше указать точный адрес)
"""

import base64
import json
import os
import urllib.error
import urllib.request

GH = "https://api.github.com"


def env(name, default=""):
    return os.environ.get(name, default)


def cors():
    return {
        "Access-Control-Allow-Origin": env("ALLOW_ORIGIN", "*"),
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
        "Content-Type": "application/json; charset=utf-8",
    }


def reply(code, payload):
    return {
        "statusCode": code,
        "headers": cors(),
        "body": json.dumps(payload, ensure_ascii=False),
    }


def gh(path, method="GET", payload=None):
    req = urllib.request.Request(
        GH + path,
        method=method,
        data=json.dumps(payload).encode() if payload else None,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + env("GH_TOKEN"),
            "User-Agent": "usi-registry-proxy",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except Exception:
            body = {"message": body[:200]}
        return e.code, body


def repo_path(suffix=""):
    return "/repos/%s/%s/contents/%s%s" % (
        env("GH_OWNER"), env("GH_REPO"), env("GH_PATH", "data.json"), suffix
    )


def handler(event, context):
    method = (event or {}).get("httpMethod", "POST")
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": cors(), "body": ""}

    # разбор тела запроса
    raw = (event or {}).get("body") or "{}"
    if (event or {}).get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode()
    try:
        req = json.loads(raw)
    except Exception:
        return reply(400, {"error": "Некорректный запрос"})

    # проверка пароля
    if not env("APP_PASS") or req.get("pass") != env("APP_PASS"):
        return reply(403, {"error": "Неверный пароль"})

    action = req.get("action", "load")
    branch = env("GH_BRANCH", "main")

    # ---------- чтение текущих данных ----------
    if action == "load":
        code, j = gh(repo_path("?ref=" + branch))
        if code == 404:
            return reply(200, {"data": {"version": 1, "updated": "", "sections": []}, "sha": None})
        if code >= 300:
            return reply(502, {"error": "GitHub: " + str(j.get("message", code))})
        content = base64.b64decode(j["content"].replace("\n", "")).decode()
        return reply(200, {"data": json.loads(content), "sha": j["sha"]})

    # ---------- история правок ----------
    if action == "history":
        code, j = gh("/repos/%s/%s/commits?path=%s&sha=%s&per_page=20" % (
            env("GH_OWNER"), env("GH_REPO"), env("GH_PATH", "data.json"), branch))
        if code >= 300:
            return reply(502, {"error": "GitHub: " + str(j)[:150]})
        return reply(200, {"commits": [
            {"sha": c["sha"],
             "date": c["commit"]["author"]["date"],
             "author": c["commit"]["message"].split("—")[-1].strip()
             if "—" in c["commit"]["message"] else c["commit"]["author"]["name"],
             "message": c["commit"]["message"]}
            for c in j
        ]})

    # ---------- загрузка конкретной версии ----------
    if action == "version":
        sha = req.get("sha", "")
        if not sha:
            return reply(400, {"error": "Не указана версия"})
        code, j = gh(repo_path("?ref=" + sha))
        if code >= 300:
            return reply(502, {"error": "GitHub: " + str(j)[:150]})
        content = base64.b64decode(j["content"].replace("\n", "")).decode()
        return reply(200, {"data": json.loads(content)})

    # ---------- сохранение ----------
    if action == "save":
        data = req.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("sections"), list):
            return reply(400, {"error": "Данные повреждены, сохранение отменено"})
        if len(json.dumps(data)) > 3_000_000:
            return reply(400, {"error": "Файл слишком большой"})

        who = (req.get("who") or "сотрудник").strip()[:40]
        body = {
            "message": "Обновление реестра — " + who,
            "content": base64.b64encode(
                json.dumps(data, ensure_ascii=False, indent=1).encode()
            ).decode(),
            "branch": branch,
        }
        if req.get("sha"):
            body["sha"] = req["sha"]

        code, j = gh(repo_path(), "PUT", body)

        # кто-то сохранил раньше — сообщаем, чтобы админка предложила перезаписать
        if code in (409, 422):
            c2, cur = gh(repo_path("?ref=" + branch))
            if c2 < 300:
                if req.get("force"):
                    body["sha"] = cur["sha"]
                    code, j = gh(repo_path(), "PUT", body)
                else:
                    return reply(409, {"error": "conflict", "sha": cur["sha"]})

        if code >= 300:
            return reply(502, {"error": "GitHub: " + str(j.get("message", code))})
        return reply(200, {"ok": True, "sha": j["content"]["sha"]})

    return reply(400, {"error": "Неизвестное действие"})
