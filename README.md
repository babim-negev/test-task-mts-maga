# Kyverno MVP для SRE-тестового задания

Пилотный стенд Kubernetes + Kyverno для SRE-тестового задания.

Репозиторий рассчитан на запуск из локальной машины на чистую Debian/Ubuntu VM
в той же сети. Для развертывания стенда нужно подготовить VM, заполнить
Ansible inventory и запустить один playbook.

Решение подготовлено для задания `Kyverno MVP` из SRE-тестового задания
MTS True Tech. Исходный PDF использовался как формулировка требований, но для
проверки достаточно этого README и файлов репозитория.

## Что Должно Получиться

После выполнения инструкций получится стенд со следующими компонентами:

- развернутый single-node Kubernetes на k3s;
- GitOps-компонент Argo CD;
- контроллер входящего трафика Envoy Gateway + Gateway API;
- Prometheus и Grafana;
- Kyverno;
- Policy Reporter для визуализации состояния политик;
- репозиторий с несколькими Kyverno policies;
- автоматические тесты политик через `kyverno test`;
- CI-процесс, который падает при сломанных policy tests и может быть
  назначен обязательной проверкой для защищенной ветки `main`;
- реальную работу admission control: кластер отклоняет небезопасный manifest.

Целевая архитектура стенда:

- Kubernetes: single-node k3s на чистой Debian/Ubuntu VM;
- GitOps: Argo CD App of Apps;
- входящий трафик: Envoy Gateway + Gateway API;
- observability: kube-prometheus-stack, Prometheus, Grafana;
- policy engine: Kyverno;
- policy visibility: Policy Reporter;
- тесты политик: `kyverno test`;
- запуск выполняется через Ansible playbook.

## Рабочий Сценарий

Основной путь для запуска:

1. Подготовить чистую Ubuntu 24.04 LTS VM с 8 GB RAM.
2. Включить SSH-доступ к VM с локальной машины.
3. Настроить пользователя VM с passwordless `sudo`.
4. Указать IP VM в `ansible/inventory.ini`.
5. Запустить `ansible-playbook`.
6. Добавить выведенные playbook записи в `/etc/hosts`.
7. Открыть Argo CD, Grafana и Policy Reporter в browser.
8. Проверить, что Kyverno отклоняет небезопасный manifest.

Поддерживаемые варианты VM:

- Ubuntu 24.04 LTS `amd64` на Ubuntu/Linux host - recommended после уточнения проверяющего;
- Ubuntu 24.04 LTS `arm64` - запасной ARM-вариант для совместимых hypervisor;
- Debian 13 `amd64/arm64` - уже подготовленный fallback;
- QEMU/libvirt + Debian cloud image + bridged-сеть - проверено локально.

Для обычного локального запуска рекомендуется `Bridged Adapter` или другая
сеть, где VM получает IP, доступный с Ansible controller. NAT и localhost port
forwarding описаны как запасной вариант в VM-документации.

## Шаг 1. Подготовить VM

Поднимите чистую Ubuntu 24.04 LTS VM. Debian 13 тоже поддерживается как
fallback, если Ubuntu-образ в конкретном hypervisor недоступен.

Минимальные требования:

- 2 vCPU;
- 8 GB RAM;
- 15 GB disk minimum, 25-30 GB recommended;
- доступ в интернет с VM;
- SSH-доступ с машины, где запускается Ansible;
- пользователь с passwordless `sudo`.

Подробная инструкция по VM:

- общий вход: [docs/VM_PREPARATION.md](docs/VM_PREPARATION.md);
- VirtualBox Ubuntu/Debian: [docs/VIRTUALBOX_DEBIAN.md](docs/VIRTUALBOX_DEBIAN.md);
- WSL2 как Ansible controller: [docs/WSL_ANSIBLE.md](docs/WSL_ANSIBLE.md).

План тестирования готовых VM-образов находится в
[docs/testing/VM_IMAGES.md](docs/testing/VM_IMAGES.md).

Рекомендуемый пользователь VM для примеров:

```text
mts
```

Проверка с локальной машины должна проходить без интерактивного пароля:

```bash
ssh mts@192.168.x.x 'whoami && sudo -n true && hostname'
```

## Шаг 2. Подготовить Ansible Controller

Все команды ниже выполняются из корня репозитория:

```bash
pwd
# .../mvp-task-mts
```

Создать Python virtualenv:

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

Установить Ansible collections:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

Если команда запускается из каталога `ansible/`, используйте:

```bash
ansible-galaxy collection install -r requirements.yml
```

## Шаг 3. Заполнить Inventory

Скопировать пример:

```bash
cp ansible/inventory.example.ini ansible/inventory.ini
```

Отредактировать `ansible/inventory.ini`:

```ini
[kyverno_mvp]
kyverno-vm ansible_host=192.168.x.x ansible_user=mts ansible_ssh_private_key_file=~/.ssh/id_ed25519

[kyverno_mvp:vars]
ansible_python_interpreter=/usr/bin/python3
```

Замените `192.168.x.x` на IP вашей VM.

Проверить Ansible-доступ:

```bash
ansible all -i ansible/inventory.ini -m ping
```

Ожидаемый результат:

```text
kyverno-vm | SUCCESS => ...
```

Если VM доступна только через NAT/localhost port forwarding, используйте
пример из [docs/VIRTUALBOX_DEBIAN.md](docs/VIRTUALBOX_DEBIAN.md#inventory-для-nat--port-forwarding).

## Шаг 4. Запустить Playbook

Запустить полный bootstrap:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

Если команда запускается из каталога `ansible/`:

```bash
ansible-playbook -i inventory.ini playbook.yml
```

В конце playbook напечатает блок для `/etc/hosts` и напомнит, что kubeconfig
для локальной проверки лежит в `files/context/config.yaml`.

## Шаг 5. Добавить /etc/hosts

На машине, где открывается browser, добавьте VM IP и домены UI в `/etc/hosts`.
Playbook печатает актуальный блок автоматически.

Пример:

```text
192.168.x.x argocd.kyverno-mvp.local
192.168.x.x grafana.kyverno-mvp.local
192.168.x.x policy-reporter.kyverno-mvp.local
```

После этого UI доступны по адресам:

```text
http://argocd.kyverno-mvp.local
http://grafana.kyverno-mvp.local
http://policy-reporter.kyverno-mvp.local
```

## Шаг 6. Проверить UI И Kyverno Deny

Проверить Kubernetes node:

```bash
ssh mts@192.168.x.x 'sudo k3s kubectl get nodes -o wide'
```

Ожидаемо node находится в состоянии `Ready`.

Проверить Argo CD:

```bash
ssh mts@192.168.x.x 'sudo k3s kubectl -n argocd get pods'
```

Проверить Kyverno:

```bash
ssh mts@192.168.x.x 'sudo k3s kubectl -n kyverno get pods'
ssh mts@192.168.x.x 'sudo k3s kubectl get clusterpolicies'
```

Проверить Policy Reporter:

```bash
ssh mts@192.168.x.x 'sudo k3s kubectl -n policy-reporter get pods,svc'
```

Проверить admission deny:

```bash
ssh mts@192.168.x.x 'sudo k3s kubectl create namespace kyverno-demo --dry-run=client -o yaml | sudo k3s kubectl apply -f -'
ssh mts@192.168.x.x 'sudo k3s kubectl apply -f -' < demo/resources/bad-privileged-pod.yaml
```

Ожидаемый результат: Kubernetes API отклоняет pod с сообщением Kyverno policy
violation, например по политике `disallow-privileged-containers`.

Проверить валидный pod:

```bash
ssh mts@192.168.x.x 'sudo k3s kubectl apply -f -' < demo/resources/good-pod.yaml
```

## Что Делает Playbook

Playbook:

- проверяет, что целевая VM - Debian или Ubuntu;
- проверяет `sudo`, RAM, CPU и размер `/`;
- проверяет privilege escalation;
- переключает apt на зеркала Яндекса, если `use_russian_mirrors=true`;
- устанавливает базовые пакеты;
- включает SSH service;
- подготавливает kernel modules и sysctl для k3s;
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

Основные настройки находятся в:

```text
ansible/group_vars/all/common.yml
ansible/group_vars/all/mirrors.yml
ansible/roles/*/defaults/main.yml
```

## Kubeconfig K3s

Kubeconfig k3s создается на server-node:

```text
/etc/rancher/k3s/k3s.yaml
```

Во время запуска playbook этот kubeconfig автоматически копируется на машину,
где запускается Ansible:

```text
files/context/config.yaml
```

Локальный файл добавлен в `.gitignore`, потому что внутри лежат client
certificate/key. При копировании Ansible заменяет адрес API server с
`127.0.0.1` на `ansible_host` из inventory.

Пример локальной проверки:

```bash
kubectl --kubeconfig files/context/config.yaml get nodes -o wide
```

Если кластер уже поднят и нужно только пересоздать локальный kubeconfig:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --tags k3s_kubeconfig
```

Если VM доступна через NAT/localhost port forwarding, для локального `kubectl`,
Lens или OpenLens нужен tunnel до Kubernetes API. Пример есть в
[docs/VIRTUALBOX_DEBIAN.md](docs/VIRTUALBOX_DEBIAN.md#nat-только-как-запасной-вариант).

## GUI-Сервисы И Port-forward

Основной способ открыть UI - через Envoy Gateway и записи в `/etc/hosts`.

Все сервисы, предназначенные для ручного просмотра через browser/port-forward,
имеют `gui` в имени:

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

Grafana доступна для просмотра состояния стенда без отдельной настройки учетной
записи.

## GitOps И App Of Apps

Argo CD bootstrap выполняется Ansible-ролью `argocd`. После этого Argo CD сам
подтягивает приложения из Git через root `Application`.

Root application смотрит в:

```yaml
argocd_root_application_path: gitops/apps
```

По умолчанию root application применяется автоматически и смотрит в этот же
репозиторий и ветку `main`:

```yaml
argocd_root_application_repo_url: "https://github.com/babim-negev/test-task-mts-maga.git"
argocd_root_application_target_revision: main
```

Дочерние Argo CD `Application` manifests в `gitops/apps` тоже закреплены на
ветку `main` этого публичного репозитория. Это основной сценарий сдачи:
проверяющий запускает стенд из опубликованного canonical repo, а Argo CD
синхронизирует проверенное состояние из `main`.

Если вы запускаете fork или private mirror, замените repo URL в двух местах:

- `argocd_root_application_repo_url` в `ansible/inventory.ini`, group vars или
  через `--extra-vars`;
- `repoURL` в дочерних manifests из `gitops/apps` для приложений, которые
  читают файлы этого репозитория.

В `gitops/apps` находятся дочерние приложения:

- `kyverno` - Helm chart Kyverno с ServiceMonitor для Prometheus;
- `policy-reporter` - Policy Reporter и UI;
- `policy-reporter-route` - HTTPRoute для `policy-reporter.kyverno-mvp.local`;
- `kyverno-policies` - ClusterPolicy manifests из `policies/clusterpolicies`;
- `kyverno-demo` - валидный demo namespace/workload.

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

Это означает, что невалидные новые pod/deployment manifests будут отклоняться
admission webhook.

## Тесты Политик И CI

Локально установите Kyverno CLI `v1.14.4`, чтобы версия совпадала с GitHub
Actions, и запустите:

```bash
kyverno test policies/tests
kyverno apply policies/clusterpolicies -r demo/resources/good-pod.yaml
```

В CI добавлен workflow:

```text
.github/workflows/kyverno-policy-tests.yml
```

Он запускается на `push` и `pull_request`, устанавливает Kyverno CLI и
выполняет:

```bash
kyverno test policies/tests
kyverno apply policies/clusterpolicies -r demo/resources/good-pod.yaml
```

Если политика сломана или expected outcome не совпадает с fixture, workflow
падает.

Для строгой блокировки раскатки включите protection для ветки `main` в GitHub:

- требовать pull request перед merge;
- требовать успешный status check `Проверить политики Kyverno`;
- синхронизировать Argo CD только из защищенной ветки `main`.

При такой схеме сломанная policy не попадает в `main`, а значит Argo CD не
раскатывает ее в кластер.

## Проверка Документации И Ansible

Проверить синтаксис playbook:

```bash
ansible-playbook -i ansible/inventory.example.ini ansible/playbook.yml --syntax-check
```

Посмотреть список задач:

```bash
ansible-playbook -i ansible/inventory.example.ini ansible/playbook.yml --list-tasks
```

## Удаление Стенда

Самый надежный способ очистить стенд - удалить тестовую VM целиком. Стенд
рассчитан на чистую одноразовую Debian/Ubuntu VM, поэтому пересоздание VM
быстрее и безопаснее ручной очистки Kubernetes и системных компонентов.

Если нужно остановить компоненты без удаления VM, выполните на VM:

```bash
sudo systemctl disable --now k3s
```

Для полной ручной очистки VM удалите k3s, kubeconfig и локальные systemd/host-path
данные:

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

Если `python3 -m venv .venv` не работает, установите пакет `python3-venv` на
локальной машине.

Если `ansible all -i ansible/inventory.ini -m ping` не возвращает `pong`,
проверьте:

- IP в `ansible/inventory.ini`;
- SSH-пользователя;
- путь до приватного ключа;
- что пользователь может выполнять `sudo -n true`;
- что VM доступна по сети с локальной машины.
