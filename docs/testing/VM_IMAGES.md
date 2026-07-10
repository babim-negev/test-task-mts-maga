# Тестирование VM-образов

Этот документ фиксирует порядок проверки готовых Ubuntu/Debian VM-образов
перед публикацией ссылок в README. Цель - подтвердить, что образ подходит как
базовая ОС для Ansible-развертывания Kyverno MVP.

## Статусы

Используемые статусы:

- `passed` - сценарий полностью пройден;
- `pending` - сценарий еще не запускался после последнего изменения образа;
- `failed` - сценарий запускался и завершился ошибкой;
- `blocked` - запуск невозможен из-за внешнего ограничения окружения.

## Матрица

| Образ | Платформа | Сеть | Статус | Комментарий |
| --- | --- | --- | --- | --- |
| `ubuntu-mts-test-amd64.qcow2` | libvirt/KVM на Ubuntu/Linux x86_64 | bridged | `passed` | 2026-07-08: минимальный чеклист и Ansible ping прошли на `bf-homelab` |
| `ubuntu-mts-test-amd64.vmdk` | VirtualBox/VMware на x86_64 | bridged | `pending` | Нужен smoke check перед публикацией ссылки |
| `ubuntu-mts-test-arm64.qcow2` | QEMU/UTM на ARM host | bridged или NAT | `pending` | Нужен минимальный чеклист; полный playbook по возможности |
| `ubuntu-mts-test-arm64.vmdk` | ARM-compatible hypervisor | bridged или NAT | `pending` | Нужен smoke check перед публикацией ссылки |
| `debian-mts-test-amd64.qcow2` | libvirt/KVM на x86_64 | bridged | `passed` | 2026-07-08: минимальный чеклист и полный playbook прошли на `bf-homelab` |
| `debian-mts-test-amd64.vmdk` | VirtualBox на x86_64 | bridged | `pending` | Нужен отдельный прогон на x86_64 host |
| `debian-mts-test-arm64-virtualbox.vmdk` | VirtualBox на Apple Silicon | bridged | `pending` | 2026-07-08: checksum приведен к фактическому файлу; нужен повторный VirtualBox smoke check |

## Последние Прогоны

### 2026-07-08: `ubuntu amd64 qcow2` на libvirt/KVM

Окружение:

- host: `bf-homelab`;
- hypervisor: libvirt/KVM;
- сеть VM: bridge `br0`;
- VM: `ubuntu-mts-test-verify`;
- IP VM: `192.168.10.130`;
- hostname: `ubuntu-mts-test`;
- user/password: `mts/mts`;
- artifact: `ubuntu-mts-test-amd64.qcow2`.

Результат минимального чеклиста:

- VM загрузилась;
- DHCP выдал IPv4 `192.168.10.130/24`;
- SSH доступен на guest-port `22`;
- вход `mts/mts` работает;
- пользователя `debian` в Ubuntu VM нет;
- `sudo -n true` работает;
- `python3 --version` работает: `Python 3.12.3`;
- `git --version` работает: `git version 2.43.0`;
- `ansible --version` работает: `ansible [core 2.16.3]`;
- Ansible ping прошел: `ok=1`, `failed=0`, `unreachable=0`.

### 2026-07-08: Ubuntu images planned

После ответа проверяющего основной release-кандидат переключен на Ubuntu
24.04 LTS:

- `ubuntu-mts-test-amd64.qcow2`;
- `ubuntu-mts-test-amd64.vmdk`;
- `ubuntu-mts-test-arm64.qcow2`;
- `ubuntu-mts-test-arm64.vmdk`.

`amd64 qcow2` собран и прошел минимальный чеклист на `bf-homelab`. Перед
публикацией всего набора еще нужны smoke check для `amd64 vmdk`, сборка/проверка
ARM64-артефактов и, по возможности, полный `ansible-playbook` на основном
Ubuntu `amd64 qcow2`.

### 2026-07-08: `amd64 qcow2` на libvirt/KVM

Окружение:

- host: `bf-homelab`;
- hypervisor: libvirt/KVM;
- сеть VM: bridge `br0`;
- VM: `kyverno-image-test-amd64`;
- IP VM: `192.168.10.11`;
- image checksum: `43763c887e05d8110fe3b8e634c676853a84df79bd72ec285d4e2e3658127b60`.

Результат минимального чеклиста:

- VM загрузилась;
- DHCP выдал IPv4;
- SSH доступен на guest-port `22`;
- вход `debian/debian` работает;
- `sudo -n true` работает;
- `python3 --version` работает: `Python 3.13.5`;
- `git --version` работает: `git version 2.47.3`;
- `ansible --version` работает: `ansible [core 2.19.4]`;
- Ansible ping прошел: `ok=1`, `failed=0`, `unreachable=0`;
- до playbook `k3s` был `inactive`, образ стартовал как чистая базовая ОС.

Полный playbook:

- команда завершилась успешно;
- итог Ansible: `ok=92`, `changed=38`, `failed=0`, `unreachable=0`;
- node Ready: `debian-mts-test`, `v1.36.2+k3s1`, IP `192.168.10.11`;
- Argo CD applications: `root`, `kyverno`, `kyverno-demo`, `kyverno-policies`, `policy-reporter`, `policy-reporter-route` - `Synced` / `Healthy`;
- Kyverno pods: Running;
- Policy Reporter pods: Running;
- ClusterPolicies: Ready.

### 2026-07-08: `arm64 VirtualBox vmdk` на Apple Silicon

Окружение:

- host: MacBook Apple Silicon;
- VirtualBox: `7.1.10r169112`;
- artifact: `debian-mts-test-arm64-virtualbox.vmdk`.

Первичный результат:

- checksum в `SHA256SUMS`: `9280d4ef126d430fbc6df92866dcc8b238a1e8b5866993841755bc3284f68434`;
- фактический checksum файла: `56118f59fb98e8042b224db34f4517b94155bf355da1c9fb4eef7b2f430e2265`;
- из-за несовпадения checksum образ нельзя считать опубликованным release-кандидатом;
- повторный запуск VirtualBox-теста не выполнен: `VBoxManage` зависает даже на чтении списка VM;
- в `VBoxSVC.log` есть ошибки `E_ACCESSDENIED` / `The object is not ready` после перезапуска VirtualBox service.

Коррекция артефактов:

- `SHA256SUMS` обновлен до фактического checksum `56118f59fb98e8042b224db34f4517b94155bf355da1c9fb4eef7b2f430e2265`;
- обычный `debian-mts-test-arm64.vmdk` восстановлен из `debian-mts-test-arm64.qcow2`;
- `./scripts/check-artifacts.sh` проходит checksum и `qemu-img info` для всех Debian artifacts.

Перед публикацией ссылки на этот VMDK нужно заново пройти минимальный VirtualBox
чеклист.

## Чеклист Для Каждого Образа

Для каждого образа нужно зафиксировать:

- checksum совпадает с опубликованным `SHA256SUMS`;
- VM загружается до login prompt;
- сеть получает IPv4 через DHCP;
- SSH доступен на guest-port `22`;
- основной Ubuntu-пользователь `mts` может войти по SSH;
- `sudo -n true` завершается без запроса пароля;
- `python3 --version` работает;
- `git --version` работает;
- `ansible --version` работает, если Ansible входит в состав образа;
- Ansible controller выполняет `ansible all -i ansible/inventory.ini -m ping`;
- опционально: полный `ansible-playbook -i ansible/inventory.ini ansible/playbook.yml` проходит до конца.

## Минимальный Протокол Прогона

1. Создать новую VM из тестируемого образа без переиспользования старого диска.
2. Выдать VM 2-4 vCPU, 8 GB RAM и диск не меньше 30 GB.
3. Подключить VM к bridged-сети или настроить NAT с явным SSH port forwarding.
4. Найти IP VM через консоль, DHCP leases или инструменты гипервизора.
5. Проверить SSH и passwordless sudo:

   ```bash
   ssh mts@192.168.x.x 'whoami && sudo -n true && hostname'
   ```

6. Проверить базовые инструменты:

   ```bash
   ssh mts@192.168.x.x 'python3 --version && git --version && ansible --version'
   ```

7. Заполнить `ansible/inventory.ini` под IP VM и выполнить Ansible ping:

   ```bash
   ansible all -i ansible/inventory.ini -m ping
   ```

8. Для release-кандидата запустить полный playbook:

   ```bash
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
   ```

9. После прогона обновить статус в матрице и добавить дату/комментарий, если
   обнаружены ограничения конкретной архитектуры или гипервизора.

## Критерии Публикации

Ссылка на образ добавляется в публичный README только после статуса `passed` по
минимальному чеклисту. Для основного рекомендуемого образа дополнительно нужен
успешный полный `ansible-playbook`.
