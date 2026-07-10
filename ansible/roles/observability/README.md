# Роль: observability

Роль устанавливает облегченный `kube-prometheus-stack` в single-node k3s cluster и публикует Grafana через Envoy Gateway.

Версия chart по умолчанию:

```yaml
observability_chart_name: kube-prometheus-stack
observability_chart_version: "87.10.1"
```

Источник chart берется из централизованного списка `ansible/group_vars/all/mirrors.yml`:

```yaml
observability_chart_repo_key: prometheus-community
```

Для single-node MVP отключены Alertmanager, kube-scheduler/controller-manager/etcd/kube-proxy scraping и соответствующие default rules. Prometheus работает без persistent volume с коротким retention:

```yaml
observability_prometheus_retention: 6h
observability_prometheus_retention_size: 1GB
```

Grafana публикуется через HTTPRoute:

```text
http://grafana.kyverno-mvp.local
```

Для ручного просмотра через port-forward роль создает service aliases:

```text
monitoring/grafana-gui
monitoring/prometheus-gui
```

Grafana открывается без логина: включен anonymous-доступ с ролью `Viewer`, а редактирование для viewer отключено.

```yaml
observability_grafana_anonymous_enabled: true
observability_grafana_anonymous_org_role: Viewer
observability_grafana_disable_login_form: true
observability_grafana_viewers_can_edit: false
```
