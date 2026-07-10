# WSL: запуск Ansible для VirtualBox VM

Этот документ описывает Windows-сценарий:

```text
Windows + VirtualBox VM с Ubuntu/Debian
WSL2 Ubuntu как Ansible controller
Ansible по SSH подключается к Ubuntu/Debian VM
```

Нативный Windows как Ansible controller не является целевым сценарием проекта. Проще и надежнее запускать Ansible из WSL2.

## 1. Установить WSL2 Ubuntu

В PowerShell от имени пользователя:

```powershell
wsl --install -d Ubuntu
```

После установки откройте Ubuntu shell.

## 2. Поставить локальные пакеты в WSL

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip sshpass
```

`sshpass` нужен Ansible для парольного SSH-доступа к готовому образу. Временный
пароль пользователя `mts` - `mts`; `sudo` внутри образа уже настроен без пароля.

## 3. Опционально подготовить SSH key

Этот шаг можно пропустить, если используете готовый образ с парольным входом.
Ключ удобен, если вы хотите заменить временный пароль на свой доступ.

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
```

Скопируйте ключ в Ubuntu/Debian VM.

Для bridged-сети:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub mts@192.168.x.x
```

Для NAT + port forwarding `host:2222 -> guest:22` попробуйте:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub -p 2222 mts@127.0.0.1
```

Если WSL2 не видит Windows localhost, найдите IP Windows host:

```bash
ip route | awk '/default/ {print $3}'
```

И используйте его:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub -p 2222 mts@<windows-host-ip>
```

## 4. Проверить VM

Bridged-сеть:

```bash
ssh mts@192.168.x.x 'whoami && sudo -n true && hostname'
```

NAT + port forwarding:

```bash
ssh -p 2222 mts@127.0.0.1 'whoami && sudo -n true && hostname'
```

Если `sudo -n true` просит пароль или падает, настройте passwordless sudo внутри VM:

```bash
sudo usermod -aG sudo mts
echo 'mts ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/90-kyverno-mvp
sudo chmod 0440 /etc/sudoers.d/90-kyverno-mvp
```

## 5. Клонировать репозиторий и поставить Ansible

```bash
git clone https://github.com/babim-negev/test-task-mts-maga.git
cd test-task-mts-maga
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install ansible
```

## 6. Inventory для bridged-сети

```bash
cp ansible/inventory.example.ini ansible/inventory.ini
```

```ini
[kyverno_mvp]
kyverno-vm ansible_host=192.168.x.x ansible_user=mts ansible_password=mts

[kyverno_mvp:vars]
ansible_python_interpreter=/usr/bin/python3
```

Проверить:

```bash
ansible all -i ansible/inventory.ini -m ping
```

## 7. Inventory для NAT + port forwarding

Если WSL видит Windows localhost:

```ini
[kyverno_mvp]
kyverno-vm ansible_host=127.0.0.1 ansible_port=2222 ansible_user=mts ansible_password=mts

[kyverno_mvp:vars]
ansible_python_interpreter=/usr/bin/python3
```

Если не видит, замените `127.0.0.1` на Windows host IP:

```bash
ip route | awk '/default/ {print $3}'
```

## 8. Запустить playbook

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

В конце Ansible напечатает готовый блок:

```text
<VM_IP> argocd.kyverno-mvp.local
<VM_IP> grafana.kyverno-mvp.local
<VM_IP> policy-reporter.kyverno-mvp.local
```

Этот блок надо добавить в `/etc/hosts` той системы, где открывается browser.

Если browser открыт в Windows, редактируйте:

```text
C:\Windows\System32\drivers\etc\hosts
```

Если browser открыт внутри Linux desktop/WSL GUI, редактируйте Linux `/etc/hosts`.
