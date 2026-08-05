#!/usr/bin/env python3
"""
Проверка ссылок реестра ЮСИ.

Запуск:
    python3 check_links.py              # берёт data.csv рядом со скриптом
    python3 check_links.py другой.csv

Что делает: открывает каждую ссылку, пишет код ответа, помечает битые.
Отчёт сохраняется в link-report.html и печатается в консоль.
"""
import csv, re, sys, ssl, json, datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor

SRC = sys.argv[1] if len(sys.argv) > 1 else 'data.csv'
URL_RE = re.compile(r'https?://[^\s,;"\'<>]+')
UA = {'User-Agent': 'Mozilla/5.0 (compatible; USI-link-check/1.0)'}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def collect(path):
    """Собирает пары (раздел, подпись, ссылка) из CSV."""
    out, section = [], ''
    with open(path, encoding='utf-8-sig', newline='') as f:
        for row in csv.reader(f):
            a = (row[0] if row else '').strip()
            b = (row[1] if len(row) > 1 else '').strip()
            if a and not b:
                section = a.rstrip(':')
                continue
            for line in (b or a).split('\n'):
                line = line.strip()
                if not line:
                    continue
                urls = URL_RE.findall(line)
                if not urls:
                    out.append((section, line, None))
                    continue
                label = URL_RE.split(line)[0].strip() or a or section
                for u in urls:
                    out.append((section, label, u))
    return out


def check(item):
    section, label, url = item
    if not url:
        return (section, label, '', 'НЕТ ССЫЛКИ')
    try:
        req = Request(url, headers=UA, method='GET')
        with urlopen(req, timeout=20, context=CTX) as r:
            code = r.status
        status = 'ок' if code < 400 else 'код %d' % code
    except HTTPError as e:
        status = 'ок' if e.code in (403, 405) else 'код %d' % e.code
    except URLError as e:
        status = 'нет ответа: %s' % e.reason
    except Exception as e:
        status = 'ошибка: %s' % e
    return (section, label, url, status)


def main():
    items = collect(SRC)
    print('Проверяю %d ссылок из %s …\n' % (len(items), SRC))
    with ThreadPoolExecutor(max_workers=12) as ex:
        res = list(ex.map(check, items))

    bad = [r for r in res if r[3] != 'ок']
    for s, l, u, st in bad:
        print('  %-28s %-34s %s' % (s[:28], l[:34], st))

    print('\nВсего: %d · рабочих: %d · с проблемами: %d'
          % (len(res), len(res) - len(bad), len(bad)))

    rows = ''.join(
        '<tr class="%s"><td>%s</td><td>%s</td><td><a href="%s">%s</a></td><td>%s</td></tr>'
        % ('bad' if st != 'ок' else '', s, l, u or '', (u or '—')[:70], st)
        for s, l, u, st in res)
    html = """<!doctype html><meta charset=utf-8><title>Отчёт по ссылкам ЮСИ</title>
<style>body{font:14px system-ui;margin:24px;color:#12203F}
h1{font-size:19px}table{border-collapse:collapse;width:100%%;font-size:12.5px}
td{border-bottom:1px solid #E2E9F5;padding:6px}
tr.bad{background:#FEF2F2}tr.bad td:last-child{color:#B42318;font-weight:700}
a{color:#1B45B8}</style>
<h1>Отчёт по ссылкам · %s</h1>
<p>Всего %d · рабочих %d · с проблемами <b>%d</b></p>
<table>%s</table>""" % (datetime.datetime.now().strftime('%d.%m.%Y %H:%M'),
                        len(res), len(res) - len(bad), len(bad), rows)
    open('link-report.html', 'w', encoding='utf-8').write(html)
    print('Отчёт сохранён: link-report.html')


if __name__ == '__main__':
    main()
