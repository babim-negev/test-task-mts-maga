# VirtualBox: Debian VM для Kyverno MVP

Скачиваемый образ в самый верх:

- официальный Debian netinst ISO: https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-13.5.0-amd64-netinst.iso
- каталог с актуальным ISO и checksum: https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/
- зеркало Яндекса, если официальный CDN недоступен: https://mirror.yandex.ru/debian-cd/current/amd64/iso-cd/
- VirtualBox downloads: https://www.virtualbox.org/wiki/Downloads

Этот путь нужен для проверяющего, который не использует libvirt/KVM и хочет поднять обычную VM в VirtualBox.

## Рекомендуемые параметры VM

Создайте новую VM:

- Type: `Linux`;
- Version: `Debian (64-bit)`;
- CPU: 4 vCPU recommended, 2 vCPU minimum;
- RAM: 8 GB;
- Disk: 30 GB dynamically allocated;
- Network: `Bridged Adapter` preferred.

`Bridged Adapter` удобнее для проверки: VM получит IP из вашей локальной сети, а Ansible сможет подключиться к ней по SSH напрямую.

Если bridged-сеть недоступна, используйте `NAT` + port forwarding:

- host port: `2222`;
- guest port: `22`.

## Установка Debian

Загрузите VM с `debian-13.5.0-amd64-netinst.iso`.

Во время установки:

- hostname: `kyverno-vm`;
- username: `debian`;
- root password можно не задавать, если installer предлагает оставить root disabled;
- установите SSH server, если installer предлагает выбор software;
- desktop environment не нужен.

Пользователь `debian` выбран намеренно: он уже указан в `ansible/inventory.example.ini`.

## Подготовка VM после первого boot

Зайдите в VM через VirtualBox console и выполните:

```bash
sudo apt update
sudo apt install -y openssh-server python3 sudo
sudo systemctl enable --now ssh
```

Рекомендуется passwordless sudo для одноразовой тестовой VM:

```bash
sudo usermod -aG sudo debian
echo 'debian ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/90-kyverno-mvp
sudo chmod 0440 /etc/sudoers.d/90-kyverno-mvp
```

Проверьте:

```bash
sudo -n true
```

Команда должна завершиться без запроса пароля.

## SSH key

На машине, где будет запускаться Ansible, создайте ключ, если его еще нет:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
```

Скопируйте публичный ключ в VM. Для bridged-сети:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub debian@192.168.x.x
```

Если `ssh-copy-id` недоступен, добавьте содержимое `~/.ssh/id_ed25519.pub` в файл VM:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo 'ssh-ed25519 AAAA... user@host' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Проверьте SSH:

```bash
ssh debian@192.168.x.x 'whoami && sudo -n true && hostname'
```

Ожидаемо:

```text
debian
kyverno-vm
```

## Inventory для bridged-сети

Скопируйте example inventory:

```bash
cp ansible/inventory.example.ini ansible/inventory.ini
```

Пример:

```ini
[kyverno_mvp]
kyverno-vm ansible_host=192.168.x.x ansible_user=debian ansible_ssh_private_key_file=~/.ssh/id_ed25519

[kyverno_mvp:vars]
ansible_python_interpreter=/usr/bin/python3
```

Проверьте Ansible-доступ:

```bash
ansible all -i ansible/inventory.ini -m ping
```

Ожидаемо:

```text
kyverno-vm | SUCCESS => ...
```

## Inventory для NAT + port forwarding

Если VirtualBox VM использует NAT и проброс `host:2222 -> guest:22`, inventory на Linux/macOS обычно выглядит так:

```ini
[kyverno_mvp]
kyverno-vm ansible_host=127.0.0.1 ansible_port=2222 ansible_user=debian ansible_ssh_private_key_file=~/.ssh/id_ed25519

[kyverno_mvp:vars]
ansible_python_interpreter=/usr/bin/python3
```

Если Ansible запускается из WSL2, `127.0.0.1:2222` может указывать на сам WSL, а не на Windows host. В этом случае используйте IP Windows host из WSL:

```bash
ip route | awk '/default/ {print $3}'
```

И подставьте его в `ansible_host`.

## Запуск

После успешного `ansible ping` вернитесь в основной README и выполните раздел `Ansible Запуск`:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

В конце playbook напечатает готовый блок для `/etc/hosts` в копируемом виде.
