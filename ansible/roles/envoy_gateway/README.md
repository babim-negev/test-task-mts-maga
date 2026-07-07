# Роль: envoy_gateway

Роль устанавливает Envoy Gateway через официальный release manifest и создает базовые Gateway API resources для входящего HTTP-трафика.

Версия по умолчанию:

```yaml
envoy_gateway_version: "v1.8.1"
```

Manifest устанавливает namespace `envoy-gateway-system` и CRD, необходимые для Gateway API и Envoy Gateway.

После установки роль применяет:

- `GatewayClass`;
- `Gateway` с HTTP listener на порту `80`;
- service alias `argocd-gui` для ручного port-forward к Argo CD UI;
- `HTTPRoute` для Argo CD UI по hostname `argocd.kyverno-mvp.local`.

Для локальной проверки добавьте IP VM в `/etc/hosts` на машине проверяющего:

```text
192.168.10.250 argocd.kyverno-mvp.local
```

Затем откройте:

```text
http://argocd.kyverno-mvp.local
```
