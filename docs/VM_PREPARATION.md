# Подготовка VM

Проверяющий поднимает чистую Debian/Ubuntu VM самостоятельно, настраивает SSH-доступ и указывает IP в `ansible/inventory.ini`.

Скачиваемый образ Debian для обычной установки в VirtualBox:

```text
https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-13.5.0-amd64-netinst.iso
```

Актуальный каталог с ISO и checksum:

```text
https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/
```

Если официальный CDN недоступен, можно взять ISO с зеркала Яндекса:

```text
https://mirror.yandex.ru/debian-cd/current/amd64/iso-cd/
```

Быстрые ссылки:

- VirtualBox + Debian ISO: [VIRTUALBOX_DEBIAN.md](VIRTUALBOX_DEBIAN.md);
- WSL2 как Ansible controller: [WSL_ANSIBLE.md](WSL_ANSIBLE.md);
- libvirt/KVM + cloud-init: раздел ниже.

Минимальные требования:

- 2 vCPU;
- 8 GB RAM;
- 15 GB disk minimum, 25-30 GB recommended for a comfortable margin;
- доступ в интернет с VM;
- SSH-доступ с машины, где запускается Ansible;
- пользователь с passwordless `sudo`.

Рекомендуемый вариант для быстрого воспроизведения стенда - Debian cloud image + cloud-init. Такой путь проверялся в homelab через libvirt/KVM.

Для VirtualBox проще использовать обычный Debian netinst ISO и ручную установку пользователя `debian`.

Рекомендуемый пользователь VM для всех вариантов:

```text
debian
```

Для одноразовой тестовой VM рекомендуется passwordless sudo:

```text
debian ALL=(ALL) NOPASSWD:ALL
```

## Вариант A: libvirt/KVM + cloud-init

Скачать Debian GenericCloud image:

```bash
curl -LO https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2
```

Если нужен более консервативный образ Debian 12:

```bash
curl -LO https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2
```

Создать overlay-диск для VM:

```bash
qemu-img create \
  -f qcow2 \
  -F qcow2 \
  -b debian-13-genericcloud-amd64.qcow2 \
  kyverno-mvp.qcow2 \
  30G
```

Создать файл `user-data` для cloud-init. В `ssh_authorized_keys` укажите публичный SSH-ключ проверяющего:

```yaml
#cloud-config
hostname: kyverno-mvp
manage_etc_hosts: true
users:
  - name: debian
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
instance-id: kyverno-mvp
local-hostname: kyverno-mvp
```

Собрать cloud-init seed ISO:

```bash
cloud-localds seed.iso user-data meta-data
```

Если `cloud-localds` не установлен, для Debian/Ubuntu он находится в пакете `cloud-image-utils`.

Альтернативный вариант, если на hypervisor нет `cloud-localds`, но есть `genisoimage` или `mkisofs`:

```bash
genisoimage \
  -output seed.iso \
  -volid cidata \
  -joliet \
  -rock \
  user-data \
  meta-data
```

Запустить VM через libvirt. Для homelab использовался bridge `br0`; если у вас другая сеть, замените `--network bridge=br0,model=virtio` на свой вариант:

```bash
virt-install \
  --name kyverno-mvp \
  --memory 8192 \
  --vcpus 4 \
  --import \
  --os-variant debian13 \
  --boot uefi \
  --disk path=kyverno-mvp.qcow2,format=qcow2,bus=virtio \
  --disk path=seed.iso,device=cdrom \
  --network bridge=br0,model=virtio \
  --graphics none \
  --noautoconsole
```

После старта VM найти ее IP можно через DHCP leases libvirt-сети, через консоль гипервизора или через `qemu-guest-agent`, если он доступен. Затем проверить SSH:

```bash
ssh debian@192.168.x.x
```

## Вариант B: VirtualBox на Windows/Linux/macOS

VirtualBox тоже подходит. Рекомендуемый путь - обычная установка Debian из netinst ISO, создание пользователя `debian`, включение SSH и passwordless sudo.

Подробный гайд: [VIRTUALBOX_DEBIAN.md](VIRTUALBOX_DEBIAN.md).

Если Ansible запускается с Windows-машины, используйте WSL2 как controller.

Подробный гайд: [WSL_ANSIBLE.md](WSL_ANSIBLE.md).

## Вариант C: ручная установка из ISO

Если cloud-init неудобен, можно поставить обычную Debian/Ubuntu VM вручную, создать пользователя с SSH-доступом и passwordless `sudo`, затем продолжить с раздела "Ansible Запуск" в основном README.

Не используйте образы с публичными default credentials как основной путь. У официальных Debian/Ubuntu cloud images обычно нет безопасного SSH-пароля по умолчанию: доступ задается через cloud-init, metadata service или ручную настройку через консоль VM. Для тестового стенда безопаснее поставить систему из официального ISO и явно настроить своего пользователя.

Рекомендуемый установочный образ Debian:

```text
https://mirror.yandex.ru/debian-cd/current/amd64/iso-cd/debian-13.5.0-amd64-netinst.iso
```

Checksum:

```text
95838884f5ea6c82421dfe6baaa5a639dbbe6756c1e380f9fe7a7cb0c1949d2a  debian-13.5.0-amd64-netinst.iso
```

Эта ссылка и checksum проверялись 2026-07-07. Если каталог `current` обновился, возьмите актуальный `debian-*-amd64-netinst.iso` и его checksum из:

```text
https://mirror.yandex.ru/debian-cd/current/amd64/iso-cd/
https://mirror.yandex.ru/debian-cd/current/amd64/iso-cd/SHA256SUMS
```

`netinst.iso` - минимальный установщик Debian. Он ставит базовую систему, а остальные пакеты подтягивает из apt-репозиториев.

После установки через консоль VM проверьте базовые пакеты и SSH:

```bash
sudo apt update
sudo apt install -y openssh-server python3 sudo
sudo systemctl enable --now ssh
```

Пользователь, указанный в `ansible/inventory.ini`, должен уметь выполнять `sudo` без интерактивного пароля. Для одноразовой тестовой VM это можно настроить так:

```bash
sudo usermod -aG sudo <user>
echo '<user> ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/90-kyverno-mvp
sudo chmod 0440 /etc/sudoers.d/90-kyverno-mvp
```

Замените `<user>` на имя пользователя VM, например `debian` или имя, созданное во время установки. После этого добавьте публичный SSH-ключ в `~/.ssh/authorized_keys` этого пользователя и проверьте вход по SSH с машины, где будет запускаться Ansible.
