# Подготовка VM

Проверяющий поднимает чистую Debian/Ubuntu VM самостоятельно, настраивает SSH-доступ и указывает IP в `ansible/inventory.ini`.

Минимальные требования:

- 2 vCPU;
- 8 GB RAM;
- 15 GB disk minimum, 25-30 GB recommended for a comfortable margin;
- доступ в интернет с VM;
- SSH-доступ с машины, где запускается Ansible;
- пользователь с passwordless `sudo`.

Рекомендуемый вариант для быстрого воспроизведения стенда - Debian cloud image + cloud-init. Такой путь проверялся в homelab через libvirt/KVM.

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

## Вариант B: VirtualBox на Windows

VirtualBox тоже подходит, но cloud image в формате `qcow2` надо подготовить отдельно. Самый простой путь на Windows - использовать WSL2 или любую Linux-машину для подготовки диска и seed ISO, а саму VM запустить в VirtualBox.

В WSL/Linux скачать образ и сконвертировать его в VDI:

```bash
curl -LO https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2
qemu-img convert -O vdi debian-13-genericcloud-amd64.qcow2 kyverno-mvp.vdi
```

Размер виртуального диска можно увеличить:

```bash
VBoxManage modifymedium disk kyverno-mvp.vdi --resize 30720
```

Далее создать `user-data`, `meta-data` и `seed.iso` так же, как в варианте libvirt:

```bash
cloud-localds seed.iso user-data meta-data
```

В VirtualBox:

- создать Linux VM: Debian 64-bit;
- выделить минимум 2 vCPU и 8 GB RAM;
- подключить `kyverno-mvp.vdi` как основной диск;
- подключить `seed.iso` как optical drive;
- выбрать сетевой режим `Bridged Adapter`, чтобы VM получила IP из той же сети, где находится машина с Ansible;
- запустить VM и дождаться завершения cloud-init.

После запуска проверить SSH:

```bash
ssh debian@192.168.x.x
```

Если bridged-сеть в VirtualBox недоступна или мешает VPN, можно использовать `NAT` + port forwarding:

- VM network: `NAT`;
- port forwarding rule: host `127.0.0.1:2222` -> guest `22`;
- inventory указывать с дополнительным SSH-port.

Пример inventory для такого варианта:

```ini
[kyverno_mvp]
kyverno-vm ansible_host=127.0.0.1 ansible_port=2222 ansible_user=debian ansible_ssh_private_key_file=~/.ssh/id_rsa

[kyverno_mvp:vars]
ansible_python_interpreter=/usr/bin/python3
```

Ansible лучше запускать из WSL/Linux/macOS. Нативный Windows как Ansible controller не является целевым сценарием этого проекта.

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
