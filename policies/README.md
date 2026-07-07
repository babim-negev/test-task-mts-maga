# Политики Kyverno

Политики лежат в `clusterpolicies`, тесты - в `tests`.

Локальная проверка:

Используйте Kyverno CLI `v1.14.4`, как в GitHub Actions.

```bash
kyverno test policies/tests
kyverno apply policies/clusterpolicies -r demo/resources/good-pod.yaml
```

CI выполняет те же проверки в `.github/workflows/kyverno-policy-tests.yml`.

Невалидные demo manifests намеренно лежат в `demo/resources`, а не в `demo/gitops`: Argo CD не должен пытаться синхронизировать ресурсы, которые Kyverno обязан отклонить.
