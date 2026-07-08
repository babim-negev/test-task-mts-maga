# Роль: k3s

## Назначение

Роль устанавливает single-node Kubernetes через k3s без `.sh`-скриптов и без официального `install.sh`.

## Подход

Роль скачивает pinned k3s binary напрямую из GitHub Releases, кладет его в versioned path и создает symlink `/usr/local/bin/k3s`.

Источник задается переменной:

```yaml
k3s_binary_url: "https://github.com/k3s-io/k3s/releases/download/{{ k3s_version }}/k3s"
k3s_binary_download_timeout: 60
k3s_binary_download_retries: 5
k3s_binary_download_delay: 10
```

## Основные переменные

```yaml
k3s_version: "v1.36.2+k3s1"
k3s_binary_versioned_path: "/usr/local/bin/k3s-{{ k3s_version }}"
k3s_binary_path: /usr/local/bin/k3s
k3s_force_download: false
k3s_binary_download_timeout: 60
k3s_binary_download_retries: 5
k3s_binary_download_delay: 10
k3s_config_dir: /etc/rancher/k3s
k3s_kubeconfig_path: /etc/rancher/k3s/k3s.yaml
k3s_local_kubeconfig_enabled: true
k3s_local_kubeconfig_path: "{{ playbook_dir }}/../files/context/config.yaml"
k3s_local_kubeconfig_server_host: "{{ ansible_host | default(inventory_hostname) }}"
k3s_local_kubeconfig_server_url: "https://{{ k3s_local_kubeconfig_server_host }}:6443"
k3s_disable_components:
  - traefik
k3s_write_kubeconfig_mode: "0644"
k3s_service_state: started
k3s_service_enabled: true
```

## Что создается на VM

- `/etc/rancher/k3s/config.yaml`;
- `/usr/local/bin/k3s-<version>`;
- symlink `/usr/local/bin/k3s`;
- systemd unit `/etc/systemd/system/k3s.service`;
- symlink `/usr/local/bin/kubectl`.

Повторный запуск не скачивает k3s binary заново, если versioned file уже существует. Для принудительной повторной загрузки используйте:

```yaml
k3s_force_download: true
```

## Проверки роли

Роль ждет:

- появления kubeconfig;
- готовности Kubernetes API через `/readyz`;
- состояния `Ready` у node;
- отсутствия deployment `traefik` в namespace `kube-system`.

## Сетевое решение

Встроенный Traefik отключается, чтобы не конфликтовать с будущим Envoy Gateway. k3s ServiceLB оставлен включенным и будет проверяться на этапе публикации Envoy Gateway через `LoadBalancer` service.

## Результат

После успешного выполнения на VM работает single-node k3s cluster, доступный через:

```bash
sudo k3s kubectl get nodes -o wide
```

Kubeconfig находится на server-node в файле:

```text
/etc/rancher/k3s/k3s.yaml
```

Роль также сохраняет kubeconfig на машине, где запускается Ansible:

```text
files/context/config.yaml
```

В локальном файле `server: https://127.0.0.1:6443` автоматически заменяется на `k3s_local_kubeconfig_server_url`. Для bridged VM обычно достаточно IP из inventory. Для localhost/NAT/QEMU-сценария используйте `k3s_local_kubeconfig_server_host=127.0.0.1` и поднимите SSH tunnel:

```bash
ssh -N -L 6443:127.0.0.1:6443 -p 2022 debian@127.0.0.1
```

Файл предназначен для `kubectl`/Lens/OpenLens и игнорируется git.

Если кластер уже поднят, локальный kubeconfig можно пересоздать без полного bootstrap:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --tags k3s_kubeconfig
```
