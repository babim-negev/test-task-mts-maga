# GitOps-Приложения

Этот каталог используется root `Application` Argo CD в App of Apps pattern.

Дочерние `Application` manifests смотрят в ветку `main` этого же публичного
репозитория:

```text
https://github.com/babim-negev/test-task-mts-maga.git
```

Если стенд запускается из fork или private mirror, нужно заменить `repoURL` в
дочерних manifests, которые читают файлы этого репозитория, и отдельно
переопределить root application URL в Ansible.

Ожидаемая цепочка:

- `root` читает `gitops/apps`;
- `kyverno` устанавливает Kyverno chart;
- `policy-reporter` устанавливает Policy Reporter chart;
- `policy-reporter-route` создает service alias `policy-reporter-gui` и публикует Policy Reporter UI через Envoy Gateway;
- `kyverno-policies` применяет политики из `policies/clusterpolicies`;
- `kyverno-demo` применяет только валидные demo resources.
