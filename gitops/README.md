# GitOps-Приложения

Этот каталог используется root `Application` Argo CD в App of Apps pattern.

Дочерние `Application` manifests смотрят в этот же репозиторий:

```text
https://github.com/babim-negev/test-task-mts-maga.git
```

Ожидаемая цепочка:

- `root` читает `gitops/apps`;
- `kyverno` устанавливает Kyverno chart;
- `policy-reporter` устанавливает Policy Reporter chart;
- `policy-reporter-route` создает service alias `policy-reporter-gui` и публикует Policy Reporter UI через Envoy Gateway;
- `kyverno-policies` применяет политики из `policies/clusterpolicies`;
- `kyverno-demo` применяет только валидные demo resources.
