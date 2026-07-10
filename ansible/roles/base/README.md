# Роль: base

## Назначение

Роль приводит чистую Debian/Ubuntu VM к базовому состоянию, достаточному для установки single-node k3s на следующем шаге playbook.

## Что устанавливается

Список пакетов по умолчанию задается переменной `base_packages` в `ansible/roles/base/defaults/main.yml`.

По умолчанию устанавливаются:

- `apt-transport-https`
- `ca-certificates`
- `curl`
- `git`
- `gnupg`
- `jq`
- `lsb-release`
- `openssh-server`
- `python3`
- `python3-apt`
- `sudo`
- `tar`
- `unzip`

## Что настраивается

- service `ssh` включается и запускается;
- загружаются kernel modules для Kubernetes networking:
  - `br_netfilter`
  - `overlay`
- modules сохраняются в `/etc/modules-load.d/kyverno-mvp-k3s.conf`;
- sysctl-настройки сохраняются в `/etc/sysctl.d/99-kyverno-mvp-k3s.conf`;
- применяется `sysctl --system`, если sysctl-файл изменился.

## Входные переменные

```yaml
base_packages:
  - ...

kernel_modules:
  - br_netfilter
  - overlay

sysctl_settings:
  net.ipv4.ip_forward: "1"
  net.bridge.bridge-nf-call-iptables: "1"
```

## Результат

VM подготовлена на уровне системных пакетов, SSH service и kernel/sysctl-настроек для Kubernetes.
