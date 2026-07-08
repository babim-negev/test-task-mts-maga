# Роль: argocd

## Назначение

Роль устанавливает Argo CD в single-node k3s cluster и проверяет, что control plane Argo CD готов к дальнейшему GitOps bootstrap.

## Подход

Argo CD устанавливается без `.sh`-скриптов через официальный Kubernetes manifest, закрепленный на конкретной версии:

```yaml
argocd_version: "v3.4.4"
argocd_install_manifest_url: "https://raw.githubusercontent.com/argoproj/argo-cd/{{ argocd_version }}/manifests/install.yaml"
```

Версия `v3.4.4` взята из latest GitHub Release Argo CD на 2026-07-06.

## Основные переменные

```yaml
argocd_namespace: argocd
argocd_apply_timeout: "360s"
argocd_rollout_timeout: "600s"
argocd_force_apply: false
argocd_redis_image_override: "cr.yandex/mirror/library/redis:8.2.3-alpine"
argocd_server_insecure: true
argocd_apply_root_application: "{{ argocd_root_application_repo_url | length > 0 }}"
argocd_root_application_name: root
argocd_root_application_repo_url: "https://github.com/babim-negev/test-task-mts-maga.git"
argocd_root_application_target_revision: main
argocd_root_application_path: gitops/apps
```

## Что делает роль

- создает namespace `argocd`, если он отсутствует;
- скачивает install manifest Argo CD в локальный файл на VM;
- заменяет Redis image из upstream manifest на `argocd_redis_image_override` до применения;
- проверяет, что подготовленный manifest не использует upstream Redis registry;
- применяет подготовленный install manifest Argo CD, если Argo CD еще не установлен;
- закрепляет Redis image на значении `argocd_redis_image_override`;
- включает `server.insecure=true`, чтобы Argo CD UI можно было публиковать через HTTP Gateway;
- ждет rollout всех deployments;
- ждет rollout всех statefulsets;
- ждет готовности всех pods;
- опционально создает root `Application` для App of Apps.

## Root Application

Root application по умолчанию применяется, потому что URL опубликованного репозитория уже задан:

```yaml
argocd_apply_root_application: "{{ argocd_root_application_repo_url | length > 0 }}"
argocd_root_application_repo_url: "https://github.com/babim-negev/test-task-mts-maga.git"
```

По умолчанию root application и дочерние приложения синхронизируются из
ветки `main` публичного репозитория сдачи.

Для fork или private mirror нужно заменить repo URL и в root application, и в
дочерних Application manifests из `gitops/apps`, потому Argo CD читает эти
файлы уже из Git:

```yaml
argocd_root_application_repo_url: "https://github.com/my-org/my-fork.git"
argocd_root_application_target_revision: main
argocd_root_application_path: gitops/apps
```

Для принудительного повторного применения install manifest используйте:

```yaml
argocd_force_apply: true
```

## Результат

После успешного выполнения Argo CD работает в namespace `argocd`:

```bash
sudo k3s kubectl -n argocd get pods
```
