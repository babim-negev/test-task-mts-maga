# Роль: helm

Роль устанавливает закрепленный Helm binary без `.sh`-скриптов.

Версия по умолчанию:

```yaml
helm_version: "v4.2.2"
```

Helm скачивается из официального источника:

```text
https://get.helm.sh/helm-v4.2.2-linux-amd64.tar.gz
```

Повторный запуск не скачивает архив заново, если versioned binary уже есть на VM. Для принудительной повторной загрузки можно выставить:

```yaml
helm_force_download: true
```
