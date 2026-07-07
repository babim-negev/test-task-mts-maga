# Роль: apt_mirrors

## Назначение

Роль переключает apt repositories на российские зеркала Яндекса, если включена переменная `use_russian_mirrors`.

## Условие запуска

```yaml
use_russian_mirrors: true
```

Если значение `false`, роль оставляет текущие apt sources без изменений.

## Используемые зеркала

Для Debian:

- `https://mirror.yandex.ru/debian/`
- `https://mirror.yandex.ru/debian-security/`

Для Ubuntu:

- `https://mirror.yandex.ru/ubuntu/`

## Что меняется

- создается директория backup: `/etc/apt/sources.backup`;
- текущий `/etc/apt/sources.list` сохраняется в backup, если файл существует;
- существующие snippets из `/etc/apt/sources.list.d` сохраняются в backup и отключаются через суффикс `.disabled`;
- создается managed source file:
  `/etc/apt/sources.list.d/kyverno-mvp-yandex.sources`;
- выполняется `apt update`.

## Важное ограничение

Роль переключает только apt repositories. Она не обещает российские зеркала для GitHub Releases, Helm charts или других внешних artifacts.

## Результат

После успешного выполнения системные пакеты устанавливаются через apt-зеркала Яндекса.
