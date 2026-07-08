# Подготовка VM

Этот документ отвечает только на вопрос: как получить чистую Debian/Ubuntu VM,
до которой Ansible сможет достучаться по SSH.

После подготовки VM вернитесь в основной README к разделу
[Шаг 2. Подготовить Ansible Controller](../README.md#шаг-2-подготовить-ansible-controller).

## Требования

Минимальные требования:

- Debian или Ubuntu;
- 2 vCPU;
- 8 GB RAM, в VirtualBox указывайте минимум `8192 MB`;
- 15 GB disk minimum, 25-30 GB recommended;
- доступ в интернет с VM;
- SSH-доступ с машины, где запускается Ansible;
- пользователь с passwordless `sudo`.

Рекомендуемый пользователь Ubuntu VM для всех примеров:

```text
mts
```

Для одноразовой тестовой VM рекомендуется passwordless sudo:

```text
mts ALL=(ALL) NOPASSWD:ALL
```

Базовая проверка с Ansible controller:

```bash
ssh mts@192.168.x.x 'whoami && sudo -n true && hostname'
```

## Рекомендуемый Путь: Ubuntu + VirtualBox + Bridged Adapter

Для локального запуска в VirtualBox рекомендуемый сетевой режим - `Bridged
Adapter`, а не NAT. Тогда VM получает обычный IP в вашей сети, Ansible
подключается к VM напрямую, а локальный kubeconfig после playbook работает без
дополнительных tunnel.

После уточнения проверяющего основной вариант - Ubuntu VM на Ubuntu/Linux host:

```text
Подготовка VM
├── Ubuntu 24.04 LTS, recommended
│   ├── amd64: ubuntu-mts-test-amd64.qcow2 или .vmdk
│   └── arm64: ubuntu-mts-test-arm64.qcow2 или .vmdk
└── Debian 13, fallback
    ├── amd64: debian-mts-test-amd64.qcow2 или .vmdk
    └── arm64: debian-mts-test-arm64.qcow2 или .vmdk
```

Короткий маршрут:

1. Скачать подходящий Ubuntu VMDK или поставить Ubuntu 24.04 LTS из ISO.
2. Создать VM в VirtualBox.
3. Выбрать `Bridged Adapter`.
4. Загрузить VM и узнать IP через `hostname -I`.
5. Проверить SSH и `sudo -n true`.
6. Вернуться в README и заполнить `ansible/inventory.ini`.

Подробный VirtualBox-гайд:

- [VIRTUALBOX_DEBIAN.md](VIRTUALBOX_DEBIAN.md).

Статус готовых образов:

- `ubuntu-mts-test-amd64.vmdk` - основной кандидат для Ubuntu/x86_64 host, требует smoke-прогона перед публикацией;
- `ubuntu-mts-test-arm64.vmdk` - ARM-кандидат, требует smoke-прогона перед публикацией;
- `debian-mts-test-arm64-virtualbox.vmdk` - проверено локально на Apple Silicon;
- `debian-mts-test-amd64.vmdk` - ссылка будет добавлена после отдельного прогона amd64/x86_64;
- ручная установка из Ubuntu ISO - запасной воспроизводимый путь без готового VMDK.

Готовые Ubuntu-образы содержат:

- пользователь: `mts`;
- пароль: `mts`;
- SSH внутри VM: port `22`;
- `sudo`: passwordless для `mts`;
- hostname: `ubuntu-mts-test`;
- сеть: DHCP.

Debian fallback сохраняет старые проверочные значения: user/password
`debian/debian`, hostname `debian-mts-test`.

## Вариант A: VirtualBox + Ubuntu ISO

Если готовый VMDK недоступен, установите Ubuntu 24.04 LTS вручную из server ISO.

Официальная страница загрузки Ubuntu Server:

```text
https://ubuntu.com/download/server
```

Официальный каталог cloud/base images и checksum:

```text
https://cloud-images.ubuntu.com/releases/24.04/release/
```

Во время установки:

- hostname: `ubuntu-mts-test`;
- username: `mts`;
- root password можно не задавать, если installer предлагает оставить root disabled;
- SSH server включить при выборе software;
- desktop environment не нужен.

После первого boot установите базовые пакеты и включите SSH:

```bash
sudo apt update
sudo apt install -y openssh-server python3 sudo git
sudo systemctl enable --now ssh
```

Настройте passwordless sudo:

```bash
sudo usermod -aG sudo mts
echo 'mts ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/90-kyverno-mvp
sudo chmod 0440 /etc/sudoers.d/90-kyverno-mvp
sudo -n true
```

Добавьте публичный SSH-ключ Ansible controller в `~/.ssh/authorized_keys`
пользователя `mts` и проверьте вход по SSH.

## Вариант B: QEMU/libvirt + cloud-init

Этот путь удобен для Linux host с libvirt/KVM. В публичной инструкции нет
привязки к конкретному bridge, IP или host: замените сетевые параметры на свои.

Скачать Ubuntu 24.04 LTS cloud image:

```bash
curl -LO https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img
```

Создать overlay-диск для VM:

```bash
qemu-img create \
  -f qcow2 \
  -F qcow2 \
  -b ubuntu-24.04-server-cloudimg-amd64.img \
  kyverno-mvp.qcow2 \
  30G
```

Создать файл `user-data`. В `ssh_authorized_keys` укажите публичный SSH-ключ
локального пользователя:

```yaml
#cloud-config
hostname: ubuntu-mts-test
manage_etc_hosts: true
users:
  - name: mts
    groups: sudo
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... user@example
package_update: true
packages:
  - qemu-guest-agent
  - python3
runcmd:
  - systemctl enable --now qemu-guest-agent
```

Создать файл `meta-data`:

```yaml
instance-id: ubuntu-mts-test
local-hostname: ubuntu-mts-test
```

Собрать cloud-init seed ISO:

```bash
cloud-localds seed.iso user-data meta-data
```

Если `cloud-localds` не установлен, для Debian/Ubuntu он находится в пакете
`cloud-image-utils`.

Альтернативный вариант, если на hypervisor нет `cloud-localds`, но есть
`genisoimage` или `mkisofs`:

```bash
genisoimage \
  -output seed.iso \
  -volid cidata \
  -joliet \
  -rock \
  user-data \
  meta-data
```

Запустить VM через libvirt. Если у вас другая сеть, замените
`--network bridge=br0,model=virtio` на свой вариант:

```bash
virt-install \
  --name kyverno-mvp \
  --memory 8192 \
  --vcpus 4 \
  --import \
  --os-variant ubuntu24.04 \
  --boot uefi \
  --disk path=kyverno-mvp.qcow2,format=qcow2,bus=virtio \
  --disk path=seed.iso,device=cdrom \
  --network bridge=br0,model=virtio \
  --graphics none \
  --noautoconsole
```

После старта VM найдите ее IP через DHCP leases, консоль hypervisor или
`qemu-guest-agent`, затем проверьте SSH:

```bash
ssh mts@192.168.x.x 'whoami && sudo -n true && hostname'
```

## Вариант C: Debian fallback

Debian 13 остается совместимым вариантом, если Ubuntu-образ в конкретной среде
недоступен. Для ручной установки используйте Debian netinst ISO:

```text
https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/
```

Требования для Debian fallback: user `debian`, passwordless sudo, SSH
guest-port `22`, hostname `debian-mts-test`, DHCP.

## Вариант D: NAT или localhost port forwarding

NAT подходит как запасной вариант, когда bridged-сеть недоступна.

Для SSH обычно достаточно port forwarding:

```text
host 127.0.0.1:2222 -> guest :22
```

Но SSH-проброс открывает только SSH. Для локального `kubectl`, Lens или
OpenLens нужен дополнительный tunnel до Kubernetes API:

```bash
ssh -N -L 6443:127.0.0.1:6443 -p 2222 mts@127.0.0.1
```

Подробности и пример inventory:

- [VIRTUALBOX_DEBIAN.md#nat-только-как-запасной-вариант](VIRTUALBOX_DEBIAN.md#nat-только-как-запасной-вариант);
- [VIRTUALBOX_DEBIAN.md#inventory-для-nat--port-forwarding](VIRTUALBOX_DEBIAN.md#inventory-для-nat--port-forwarding).

## Возврат В README

Когда VM готова и команда ниже проходит успешно:

```bash
ssh mts@192.168.x.x 'whoami && sudo -n true && hostname'
```

вернитесь в основной README:

- [Шаг 2. Подготовить Ansible Controller](../README.md#шаг-2-подготовить-ansible-controller);
- [Шаг 3. Заполнить Inventory](../README.md#шаг-3-заполнить-inventory);
- [Шаг 4. Запустить Playbook](../README.md#шаг-4-запустить-playbook).
