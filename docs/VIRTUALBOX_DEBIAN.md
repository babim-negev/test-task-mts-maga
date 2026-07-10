# VirtualBox: Ubuntu/Debian VM для Kyverno MVP

Этот документ описывает подготовку Ubuntu или Debian VM в VirtualBox до
состояния, когда Ansible может подключиться по SSH и выполнить основной
playbook. После уточнения проверяющего основной путь - Ubuntu 24.04 LTS;
Debian оставлен как fallback.

После успешной проверки SSH вернитесь в основной README:
[Шаг 2. Подготовить Ansible Controller](../README.md#шаг-2-подготовить-ansible-controller).

Полезные ссылки:

- VirtualBox downloads: https://www.virtualbox.org/wiki/Downloads
- Ubuntu Server downloads: https://ubuntu.com/download/server
- Ubuntu 24.04 cloud images и checksum: https://cloud-images.ubuntu.com/releases/24.04/release/
- официальный каталог Debian netinst ISO и checksum: https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/
- зеркало Яндекса, если официальный CDN недоступен: https://mirror.yandex.ru/debian-cd/current/amd64/iso-cd/

## Быстрый Путь: Готовый VMDK

Статус готовых дисков:

- `ubuntu-mts-test-amd64.vmdk` - основной кандидат для проверяющего на Ubuntu/x86_64 host, требует smoke-прогона перед публикацией;
- `ubuntu-mts-test-arm64.vmdk` - ARM-кандидат для совместимых ARM hypervisor, требует smoke-прогона перед публикацией;
- `debian-mts-test-arm64-virtualbox.vmdk` - проверено локально на Apple Silicon;
- `debian-mts-test-amd64.vmdk` - ссылка будет добавлена после отдельного прогона amd64/x86_64.

Готовый VMDK уже содержит:

- пользователя `mts`;
- пароль `mts`;
- SSH на guest-port `22`;
- passwordless sudo для `mts`;
- `python3`, `git`;
- hostname `ubuntu-mts-test`;
- DHCP-сеть.

В VirtualBox создайте новую VM:

- Type: `Linux`;
- Version: `Ubuntu (64-bit)` для amd64 host или ближайший доступный Linux ARM 64-bit profile для ARM host;
- CPU: 4 vCPU recommended, 2 vCPU minimum;
- RAM: `8192 MB` minimum;
- Hard Disk:
  - x86_64/amd64: `Use an Existing Virtual Hard Disk File` -> `ubuntu-mts-test-amd64.vmdk`;
  - ARM host: `Use an Existing Virtual Hard Disk File` -> `ubuntu-mts-test-arm64.vmdk`, если VirtualBox поддерживает такой guest;
  - Apple Silicon fallback: `Use an Existing Virtual Hard Disk File` -> `debian-mts-test-arm64-virtualbox.vmdk`.

Сеть настраивается в свойствах VM, а не внутри VMDK:

- Adapter 1: `Enable Network Adapter`;
- `Attached to: Bridged Adapter`;
- выберите реальный интерфейс host-машины, например Wi-Fi или Ethernet;
- NAT используйте только как запасной вариант.

После boot зайдите в консоль VM:

```text
login: mts
password: mts
```

Проверьте IP и базовые инструменты:

```bash
hostname -I
ip -4 addr show
sudo -n true
systemctl is-active ssh
python3 --version
git --version
```

Если используется свежий VMDK, SSH host keys создаются автоматически при первом
boot. Если проверяется старый артефакт и `ssh` не стартует из-за отсутствующих
host keys, выполните один раз:

```bash
sudo ssh-keygen -A
sudo systemctl restart ssh
```

Дальше настройте SSH key с Ansible controller.

## Как Найти IP VM

Если выбран `Bridged Adapter`, VM получает отдельный IP от вашей сети. Это не
`localhost` и не `2022`; SSH будет на стандартном порту `22`:

```bash
ssh mts@192.168.x.x
```

Самые простые способы узнать адрес:

1. В консоли VM выполнить:

   ```bash
   hostname -I
   ip -4 addr show
   ```

   Нужен адрес не `127.0.0.1`, обычно что-то вроде `192.168.x.x`.

2. В роутере или DHCP leases найти hostname:

   ```text
   ubuntu-mts-test
   ```

3. На Mac посмотреть ARP-соседей:

   ```bash
   arp -a | grep -i 08:00:27
   ```

   VirtualBox часто выдает VM MAC с префиксом `08:00:27`.

## SSH Key

На машине, где будет запускаться Ansible, создайте ключ, если его еще нет:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
```

Скопируйте публичный ключ в VM. Для bridged-сети:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub mts@192.168.x.x
```

Если `ssh-copy-id` недоступен, добавьте содержимое
`~/.ssh/id_ed25519.pub` в файл VM:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo 'ssh-ed25519 AAAA... user@host' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Проверьте SSH:

```bash
ssh mts@192.168.x.x 'whoami && sudo -n true && hostname'
```

Ожидаемо:

```text
mts
ubuntu-mts-test
```

## Inventory Для Bridged-Сети

В основном README этот шаг описан подробнее. Для bridged-сети inventory обычно
выглядит так:

```ini
[kyverno_mvp]
kyverno-vm ansible_host=192.168.x.x ansible_user=mts ansible_password=mts

[kyverno_mvp:vars]
ansible_python_interpreter=/usr/bin/python3
```

Для готового образа используется временный пароль `mts`; `sudo` для пользователя
`mts` уже настроен без пароля.

Проверить Ansible-доступ:

```bash
ansible all -i ansible/inventory.ini -m ping
```

Ожидаемо:

```text
kyverno-vm | SUCCESS => ...
```

## Запасной Путь: Установка Ubuntu Из ISO

Если готовый VMDK недоступен, создайте VM с обычным Ubuntu 24.04 Server ISO.

Рекомендуемые параметры VM:

- Type: `Linux`;
- Version: `Ubuntu (64-bit)`;
- CPU: 4 vCPU recommended, 2 vCPU minimum;
- RAM: `8192 MB` minimum;
- Disk: 30 GB dynamically allocated;
- Network: `Bridged Adapter` preferred.

Во время установки:

- hostname: `kyverno-vm`;
- username: `mts`;
- root password можно не задавать, если installer предлагает оставить root disabled;
- установите SSH server, если installer предлагает выбор software;
- desktop environment не нужен.

После первого boot зайдите в VM через VirtualBox console и выполните:

```bash
sudo apt update
sudo apt install -y openssh-server python3 sudo git
sudo systemctl enable --now ssh
```

Настройте passwordless sudo для одноразовой тестовой VM:

```bash
sudo usermod -aG sudo mts
echo 'mts ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/90-kyverno-mvp
sudo chmod 0440 /etc/sudoers.d/90-kyverno-mvp
sudo -n true
```

После этого настройте SSH key и проверьте вход с Ansible controller.

## Debian fallback

Если Ubuntu-образ в конкретном hypervisor недоступен, можно использовать Debian
13 VM. Для Debian fallback остаются старые значения: user `debian`,
passwordless sudo, SSH guest-port `22`, hostname `debian-mts-test`, DHCP. Для
amd64 ручной установки подходит Debian netinst ISO из официального каталога:

```text
https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/
```

## NAT Только Как Запасной Вариант

Если выбран `NAT`, отдельного LAN IP не будет. Тогда в настройках VirtualBox
нужно добавить port forwarding:

```text
host 127.0.0.1:2222 -> guest :22
```

Подключение по SSH:

```bash
ssh -p 2222 mts@127.0.0.1
```

Для второй NAT VM нельзя использовать тот же host-port `2222`; выберите
`2223`, `2224` и так далее.

Для доступа к Kubernetes API с host-машины через kubeconfig, Lens или OpenLens
при NAT нужен отдельный tunnel до guest-port `6443`:

```bash
ssh -N -L 6443:127.0.0.1:6443 -p 2222 mts@127.0.0.1
```

Если SSH host-port другой, например `2022`, замените `-p 2222` на свой порт.
После этого локальный kubeconfig должен смотреть на:

```text
server: https://127.0.0.1:6443
```

При bridged-сети tunnel обычно не нужен: kubeconfig может смотреть прямо на
IP VM, например `https://192.168.x.x:6443`.

## Inventory Для NAT + Port Forwarding

Если VirtualBox VM использует NAT и проброс `host:2222 -> guest:22`, inventory
на Linux/macOS обычно выглядит так:

```ini
[kyverno_mvp]
kyverno-vm ansible_host=127.0.0.1 ansible_port=2222 ansible_user=mts ansible_password=mts k3s_local_kubeconfig_server_host=127.0.0.1

[kyverno_mvp:vars]
ansible_python_interpreter=/usr/bin/python3
```

Если Ansible запускается из WSL2, `127.0.0.1:2222` может указывать на сам WSL,
а не на Windows host. В этом случае используйте IP Windows host из WSL:

```bash
ip route | awk '/default/ {print $3}'
```

И подставьте его в `ansible_host`.

## Возврат В README

Когда проверка проходит:

```bash
ssh mts@192.168.x.x 'whoami && sudo -n true && hostname'
```

или для NAT:

```bash
ssh -p 2222 mts@127.0.0.1 'whoami && sudo -n true && hostname'
```

вернитесь в основной README:

- [Шаг 2. Подготовить Ansible Controller](../README.md#шаг-2-подготовить-ansible-controller);
- [Шаг 3. Заполнить Inventory](../README.md#шаг-3-заполнить-inventory);
- [Шаг 4. Запустить Playbook](../README.md#шаг-4-запустить-playbook).
