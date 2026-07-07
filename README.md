# Kyverno MVP для SRE-тестового задания

Пилотный стенд Kubernetes + Kyverno для SRE-тестового задания.

Целевая архитектура стенда:

- Kubernetes: single-node k3s на чистой Debian/Ubuntu VM;
- GitOps: Argo CD;
- входящий трафик: Envoy Gateway + Gateway API;
- observability: Prometheus + Grafana;
- policy engine: Kyverno;
- policy visibility: Policy Reporter;
- тесты политик: `kyverno test`;
- запуск: Ansible, без `.sh`-оберток.

Сейчас реализованы:

- **Этап 1**: базовая подготовка VM;
- **Этап 2**: установка single-node k3s;
- **Этап 3**: bootstrap Argo CD;
- **Этап 4**: Envoy Gateway и первый HTTPRoute для Argo CD UI;
- **Этап 5**: Observability через kube-prometheus-stack и Grafana;
- **Этап 6**: GitOps App of Apps для Kyverno, Policy Reporter, политик и demo;
- **Этап 7**: политики Kyverno, `kyverno test`, CI и demo admission deny.

## Где Тестировалось

Стенд проверялся в homelab на VM `kyverno-mvp`:

- гипервизор: libvirt/KVM на `bf-homelab`;
- образ: Debian 13 GenericCloud;
- boot mode: UEFI;
- сеть: bridge `br0`;
- IP VM: `192.168.10.250`;
- SSH-пользователь: `debian`;
- ресурсы VM: 4 vCPU, 8 GB RAM, 30 GB disk.

## Быстрая Проверка За 15 Минут

1. Подготовить чистую Debian/Ubuntu VM с SSH и passwordless `sudo`.
2. Скопировать inventory:

```bash
cp ansible/inventory.example.ini ansible/inventory.ini
```

3. Указать IP VM и SSH-пользователя в `ansible/inventory.ini`.
4. Запустить bootstrap:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

5. Добавить VM IP в `/etc/hosts`:

```text
192.168.10.250 argocd.kyverno-mvp.local
192.168.10.250 grafana.kyverno-mvp.local
192.168.10.250 policy-reporter.kyverno-mvp.local
```

6. Проверить UI:

```text
http://argocd.kyverno-mvp.local
http://grafana.kyverno-mvp.local
http://policy-reporter.kyverno-mvp.local
```

7. Проверить admission deny:

```bash
ssh debian@192.168.x.x 'sudo k3s kubectl apply -f -' < demo/resources/bad-privileged-pod.yaml
```

Ожидаемый результат: Kubernetes API отклоняет pod с сообщением Kyverno policy violation.

## Подготовка VM

Проверяющий поднимает чистую VM Debian или Ubuntu самостоятельно, настраивает SSH-доступ и указывает IP в Ansible inventory.

Минимальные требования для комфортного запуска стенда:

- 2 vCPU;
- 4 GB RAM;
- 15 GB disk minimum, 25-30 GB recommended for a comfortable margin;
- доступ в интернет с VM;
- SSH-доступ с машины, где запускается Ansible;
- пользователь с passwordless `sudo`.

Подробные варианты подготовки VM вынесены в отдельный документ: [docs/VM_PREPARATION.md](docs/VM_PREPARATION.md).

Там описаны:

- libvirt/KVM + Debian cloud image + cloud-init;
- VirtualBox на Windows через WSL/Linux-подготовку образа;
- ручная установка Debian/Ubuntu из ISO без cloud-init.

## Ansible Запуск

Все команды ниже предполагают, что текущий каталог - корень репозитория:

```bash
pwd
# .../test-task-mts
```

### 1. Подготовить локальное окружение

Создать Python virtualenv в корне репозитория:

```bash
python3 -m venv .venv
```

Активировать virtualenv:

```bash
source .venv/bin/activate
```

Обновить `pip`:

```bash
python -m pip install -U pip
```

Установить Ansible:

```bash
python -m pip install ansible
```

Установить Ansible collections из репозитория:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

Сейчас `ansible/requirements.yml` пустой, поэтому команда может вывести:

```text
Skipping install, no requirements found
```

Это нормально: текущие роли используют только builtin-модули Ansible.

Если вы уже находитесь внутри каталога `ansible/`, используйте путь без дополнительного префикса:

```bash
ansible-galaxy collection install -r requirements.yml
```

### 2. Заполнить inventory

Скопировать пример inventory:

```bash
cp ansible/inventory.example.ini ansible/inventory.ini
```

Отредактировать `ansible/inventory.ini`:

```ini
[kyverno_mvp]
kyverno-vm ansible_host=192.168.x.x ansible_user=debian ansible_ssh_private_key_file=~/.ssh/id_rsa

[kyverno_mvp:vars]
ansible_python_interpreter=/usr/bin/python3
```

Для нашего `bf-homelab` VM переведена на внешний bridge `br0` и использует статический адрес:

```ini
[kyverno_mvp]
kyverno-vm ansible_host=192.168.10.250 ansible_user=debian ansible_ssh_private_key_file=~/.ssh/id_rsa
```

Перед раскаткой надо проверить SSH/Ansible-доступ.

Проверено:

```bash
ansible all -i ansible/inventory.ini -m ping
```

возвращает `pong` для `kyverno-vm`.

### 3. Проверить доступность VM

```bash
ansible all -i ansible/inventory.ini -m ping
```

### 4. Запустить playbook

Запустить playbook:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

Если вы запускаете команду из каталога `ansible/`:

```bash
ansible-playbook -i inventory.ini playbook.yml
```

В проекте намеренно нет `.sh`-скриптов: запуск должен быть прозрачным и воспроизводимым через Ansible.

## Что Делает Playbook

Playbook:

- проверяет, что целевая VM - Debian или Ubuntu;
- проверяет `sudo`, RAM, CPU и размер `/`;
- проверяет privilege escalation;
- переключает apt на зеркала Яндекса, если `use_russian_mirrors=true`;
- устанавливает базовые пакеты;
- включает SSH service;
- подготавливает kernel modules и sysctl для будущего k3s;
- устанавливает pinned k3s binary;
- настраивает single-node k3s server;
- отключает встроенный Traefik;
- оставляет k3s ServiceLB включенным;
- настраивает kubeconfig mode `0644`;
- создает symlink `/usr/local/bin/kubectl` на k3s binary;
- проверяет готовность Kubernetes API и node;
- устанавливает Argo CD в namespace `argocd`;
- проверяет rollout Argo CD deployments/statefulsets и готовность pods;
- устанавливает pinned Helm binary;
- устанавливает Envoy Gateway через официальный release manifest;
- создает `GatewayClass`, `Gateway` и `HTTPRoute` для Argo CD UI;
- устанавливает облегченный kube-prometheus-stack;
- публикует Grafana через Envoy Gateway;
- применяет root `Application` для App of Apps.

Версия k3s по умолчанию зафиксирована в `ansible/roles/k3s/defaults/main.yml`:

```yaml
k3s_version: "v1.36.2+k3s1"
```

K3s скачивается напрямую из GitHub Releases:

```text
https://github.com/k3s-io/k3s/releases/download/v1.36.2+k3s1/k3s
```

Повторный запуск не скачивает k3s binary заново, если файл уже есть на VM. Для принудительной повторной загрузки можно выставить:

```yaml
k3s_force_download: true
```

### Kubeconfig k3s

Kubeconfig k3s создается на server-node:

```text
/etc/rancher/k3s/k3s.yaml
```

Во время запуска playbook этот kubeconfig автоматически копируется на машину, где запускается Ansible:

```text
files/context/config.yaml
```

Локальный файл добавлен в `.gitignore`, потому что внутри лежат client certificate/key. При копировании Ansible заменяет адрес API server с `127.0.0.1` на `ansible_host` из inventory, например:

```yaml
server: https://192.168.10.250:6443
```

Этот файл можно импортировать в Lens/OpenLens или использовать напрямую:

```bash
kubectl --kubeconfig files/context/config.yaml get nodes -o wide
```

Если кластер уже поднят и нужно только пересоздать локальный kubeconfig:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --tags k3s_kubeconfig
```

На самой VM можно работать без копирования файла:

```bash
sudo k3s kubectl get nodes -o wide
```

Если kubeconfig нужно скачать вручную, скопируйте его с VM и замените адрес API server с `127.0.0.1` на IP или DNS-имя VM:

```bash
mkdir -p ~/.kube
ssh debian@192.168.x.x 'sudo cat /etc/rancher/k3s/k3s.yaml' > ~/.kube/config
kubectl config set-cluster default --server=https://192.168.x.x:6443
kubectl get nodes -o wide
```

Версия Argo CD по умолчанию зафиксирована в `ansible/roles/argocd/defaults/main.yml`:

```yaml
argocd_version: "v3.4.4"
```

Argo CD устанавливается из официального manifest:

```text
https://raw.githubusercontent.com/argoproj/argo-cd/v3.4.4/manifests/install.yaml
```

По умолчанию роль использует Redis image из официального manifest Argo CD. Если upstream registry недоступен в вашей сети, можно указать mirror в `ansible/group_vars/all/common.yml`:

```yaml
argocd_redis_image_override: "cr.yandex/<registry-id>/redis:8.2.3-alpine"
```

Если нужно принудительно переехать на новую версию Argo CD или повторно применить официальный manifest, выставьте `argocd_force_apply: true`.

Argo CD server переводится в insecure mode для публикации через HTTP Gateway:

```yaml
argocd_server_insecure: true
```

Версия Helm по умолчанию зафиксирована в `ansible/roles/helm/defaults/main.yml`:

```yaml
helm_version: "v4.2.2"
```

Версия Envoy Gateway по умолчанию зафиксирована в `ansible/roles/envoy_gateway/defaults/main.yml`:

```yaml
envoy_gateway_version: "v1.8.1"
```

Первый опубликованный UI - Argo CD:

```text
http://argocd.kyverno-mvp.local
```

На машине проверяющего добавьте IP VM в `/etc/hosts`:

```text
192.168.10.250 argocd.kyverno-mvp.local
192.168.10.250 grafana.kyverno-mvp.local
192.168.10.250 policy-reporter.kyverno-mvp.local
```

Версия kube-prometheus-stack по умолчанию зафиксирована в `ansible/roles/observability/defaults/main.yml`:

```yaml
observability_chart_name: kube-prometheus-stack
observability_chart_version: "87.10.1"
```

Grafana доступна без логина по адресу:

```text
http://grafana.kyverno-mvp.local
```

## GUI-Сервисы И Port-forward

Все сервисы, предназначенные для ручного просмотра через browser/port-forward, имеют `gui` в имени:

```bash
kubectl --kubeconfig files/context/config.yaml get svc -A | grep gui
```

Ожидаемые GUI services:

```text
argocd/argocd-gui
monitoring/grafana-gui
monitoring/prometheus-gui
policy-reporter/policy-reporter-gui
```

Примеры port-forward:

```bash
kubectl --kubeconfig files/context/config.yaml -n argocd port-forward svc/argocd-gui 8080:80
kubectl --kubeconfig files/context/config.yaml -n monitoring port-forward svc/grafana-gui 3000:80
kubectl --kubeconfig files/context/config.yaml -n monitoring port-forward svc/prometheus-gui 9090:9090
kubectl --kubeconfig files/context/config.yaml -n policy-reporter port-forward svc/policy-reporter-gui 8081:8080
```

Grafana доступна для просмотра состояния стенда без отдельной настройки учетной записи.

Главные переменные находятся в:

```text
ansible/group_vars/all/common.yml
ansible/group_vars/all/mirrors.yml
ansible/roles/*/defaults/main.yml
```

`group_vars/all/` содержит общие настройки стенда для любой Debian/Ubuntu VM. Файла `ansible/group_vars/all.yml` больше нет: вместо него используется директория `ansible/group_vars/all/`. Ролевые значения по умолчанию лежат рядом с ролями в `defaults/main.yml`.

Для будущих Helm-установок заведены централизованные зеркала в `ansible/group_vars/all/mirrors.yml`. Приоритетный источник для charts - зеркало Яндекса:

```text
https://mirror.yandex.ru/helm/
```

Container registry proxy `https://huecker.io/` зафиксирован как optional fallback, но не как обязательная зависимость.

Для Kyverno chart проверено рабочее зеркало Яндекса:

```text
https://mirror.yandex.ru/helm/kyverno.github.io
```

Policy Reporter использует официальный upstream Helm repository:

```text
https://kyverno.github.io/policy-reporter
```

## GitOps И App Of Apps

Argo CD bootstrap выполняется Ansible-ролью `argocd`. После этого Argo CD может сам подтянуть приложения из Git через root `Application`.

Root application смотрит в:

```yaml
argocd_root_application_path: gitops/apps
```

По умолчанию root application применяется автоматически и смотрит в этот же репозиторий:

```yaml
argocd_root_application_repo_url: "https://github.com/babim-negev/test-task-mts-maga.git"
```

Если вы запускаете fork или private mirror, переопределите `argocd_root_application_repo_url` в `ansible/inventory.ini`, group vars или через `--extra-vars`.

Дочерние `Application` manifests в `gitops/apps/*.yaml` уже смотрят в этот же репозиторий:

```text
https://github.com/babim-negev/test-task-mts-maga.git
```

В `gitops/apps` находятся дочерние приложения:

- `kyverno` - Helm chart Kyverno с ServiceMonitor для Prometheus;
- `policy-reporter` - Policy Reporter и UI;
- `policy-reporter-route` - HTTPRoute для `policy-reporter.kyverno-mvp.local`;
- `kyverno-policies` - ClusterPolicy manifests из `policies/clusterpolicies`;
- `kyverno-demo` - валидный demo namespace/workload.

Argo CD после синхронизации должен показывать цепочку:

```text
root -> kyverno
root -> policy-reporter
root -> policy-reporter-route
root -> kyverno-policies
root -> kyverno-demo
```

## Политики Kyverno

Политики лежат в `policies/clusterpolicies`:

- `disallow-privileged-containers` - запрещает privileged containers;
- `require-non-root-containers` - требует явный non-root режим;
- `disallow-latest-image-tag` - запрещает `latest` и образы без tag;
- `require-resource-requests-limits` - требует cpu/memory requests и limits.

Все политики работают в режиме:

```yaml
validationFailureAction: Enforce
```

Это означает, что невалидные новые pod/deployment manifests будут отклоняться admission webhook.

## Тесты Политик И CI

Локально установите Kyverno CLI `v1.14.4`, чтобы версия совпадала с GitHub Actions, и запустите:

```bash
kyverno test policies/tests
kyverno apply policies/clusterpolicies -r demo/resources/good-pod.yaml
```

В CI добавлен workflow:

```text
.github/workflows/kyverno-policy-tests.yml
```

Он запускается на `push` и `pull_request`, устанавливает Kyverno CLI и выполняет:

```bash
kyverno test policies/tests
kyverno apply policies/clusterpolicies -r demo/resources/good-pod.yaml
```

Если политика сломана или expected outcome не совпадает с fixture, workflow падает и блокирует безопасную раскатку через GitOps.

## Проверка

Проверить синтаксис:

```bash
ansible-playbook -i ansible/inventory.example.ini ansible/playbook.yml --syntax-check
```

Посмотреть список задач:

```bash
ansible-playbook -i ansible/inventory.example.ini ansible/playbook.yml --list-tasks
```

Проверить доступность VM:

```bash
ansible all -i ansible/inventory.ini -m ping
```

После успешного запуска playbook проверить Kubernetes:

```bash
ssh debian@192.168.x.x sudo k3s kubectl get nodes -o wide
```

Для текущей VM:

```bash
ssh -i ~/.ssh/id_rsa debian@192.168.10.250 'sudo k3s kubectl get nodes -o wide'
```

Ожидаемый результат:

```text
kyverno-mvp   Ready    control-plane   ...   v1.36.2+k3s1   192.168.10.250
```

Встроенный Traefik должен быть отключен:

```bash
ssh -i ~/.ssh/id_rsa debian@192.168.10.250 'sudo k3s kubectl -n kube-system get deploy traefik'
```

Ожидаемый результат:

```text
Error from server (NotFound): deployments.apps "traefik" not found
```

Проверить Argo CD:

```bash
ssh -i ~/.ssh/id_rsa debian@192.168.10.250 'sudo k3s kubectl -n argocd get pods -o wide'
```

Ожидаемый результат: pods Argo CD находятся в состоянии `Running` и `Ready`.

Проверить root Application для App of Apps, если задан `argocd_root_application_repo_url`:

```bash
ssh debian@192.168.x.x 'sudo k3s kubectl -n argocd get application root'
```

Проверить Kyverno:

```bash
ssh debian@192.168.x.x 'sudo k3s kubectl -n kyverno get pods'
ssh debian@192.168.x.x 'sudo k3s kubectl get clusterpolicies'
```

Проверить Policy Reporter:

```bash
ssh debian@192.168.x.x 'sudo k3s kubectl -n policy-reporter get pods,svc'
```

Проверить admission deny:

```bash
ssh debian@192.168.x.x 'sudo k3s kubectl create namespace kyverno-demo --dry-run=client -o yaml | sudo k3s kubectl apply -f -'
ssh debian@192.168.x.x 'sudo k3s kubectl apply -f -' < demo/resources/bad-privileged-pod.yaml
```

Ожидаемый результат:

```text
Error from server: admission webhook ... denied the request ... disallow-privileged-containers
```

Проверить валидный pod:

```bash
ssh debian@192.168.x.x 'sudo k3s kubectl apply -f -' < demo/resources/good-pod.yaml
```

Root Application для App of Apps применяется по умолчанию, потому что `argocd_root_application_repo_url` уже указывает на опубликованный репозиторий.

## Удаление Стенда

Самый надежный способ очистить стенд - удалить тестовую VM целиком. Стенд рассчитан на чистую одноразовую Debian/Ubuntu VM, поэтому пересоздание VM быстрее и безопаснее ручной очистки всех Kubernetes и системных компонентов.

Если нужно остановить компоненты без удаления VM, выполните на VM:

```bash
sudo systemctl disable --now k3s
```

Для полной ручной очистки VM удалите k3s, kubeconfig и локальные systemd/host-path данные:

```bash
sudo systemctl disable --now k3s || true
sudo rm -f /etc/systemd/system/k3s.service
sudo rm -f /usr/local/bin/k3s /usr/local/bin/kubectl
sudo rm -rf /etc/rancher/k3s /var/lib/rancher/k3s /var/lib/kubelet
sudo systemctl daemon-reload
```

На локальной машине можно удалить сгенерированный kubeconfig:

```bash
rm -f files/context/config.yaml
```

## Диагностика Проблем

Если `python3 -m venv .venv` не работает, установите пакет `python3-venv` на локальной машине.

Если `ansible all -i ansible/inventory.ini -m ping` не возвращает `pong`, проверьте:

- IP в `ansible/inventory.ini`;
- SSH-пользователя;
- путь до приватного ключа;
- что пользователь может выполнять `sudo`;
- что VM доступна по сети с локальной машины.

Если `ansible-galaxy collection install -r ansible/requirements.yml` пишет `Skipping install, no requirements found`, это нормально для текущего состояния проекта.
