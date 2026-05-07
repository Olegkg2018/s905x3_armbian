# Налаштування Wi-Fi точки доступу (AP) на Armbian (S905X3)

**Режим:** Роутер (NAT)  
**Підмережа Wi-Fi:** 192.168.3.x  
**Підмережа LAN:** 192.168.2.x

---

## 1️⃣ Підготовка інтерфейсів (NetworkManager)

Потрібно об'єднати провідний порт в міст (для зручності самої приставки), але залишити Wi-Fi незалежним.

### Створюємо міст для провідної мережі

```bash
sudo nmcli con add type bridge ifname br0 con-name br0
sudo nmcli con add type ethernet slave-type bridge master br0 ifname eth0 con-name eth0-br0
sudo nmcli con modify br0 ipv4.addresses 192.168.2.130/24 ipv4.gateway 192.168.2.1 ipv4.method manual
sudo nmcli con modify br0 ipv4.dns "8.8.8.8 8.8.4.4"
sudo nmcli con up br0
```

### Забороняємо NetworkManager керувати wlan0

```bash
sudo nano /etc/NetworkManager/NetworkManager.conf
```

Додайте в секцію `[keyfile]`:

```ini
unmanaged-devices=interface-name:wlan0
```

---

## 2️⃣ Встановлення та налаштування Hostapd

```bash
sudo apt install hostapd
sudo nano /etc/hostapd/hostapd.conf
```

Додайте наступну конфігурацію:

```ini
interface=wlan0
driver=nl80211
ssid=MyArmbianAP
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=ВАШ_ПАРОЛЬ
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

**Замініть:**
- `ssid=MyArmbianAP` — назву вашої Wi-Fi мережі
- `wpa_passphrase=ВАШ_ПАРОЛЬ` — пароль для Wi-Fi (мінімум 8 символів)

---

## 3️⃣ Налаштування DHCP (Dnsmasq)

```bash
sudo apt install dnsmasq
sudo nano /etc/dnsmasq.conf
```

Додайте:

```ini
interface=wlan0
bind-dynamic
dhcp-range=192.168.3.10,192.168.3.100,12h
domain-needed
bogus-priv
dhcp-option=6,8.8.8.8,8.8.4.4
```

---

## 4️⃣ Автоматизація налаштування IP

Створіть скрипт:

```bash
sudo nano /usr/local/bin/fix-wifi-ip.sh
```

Додайте:

```bash
#!/bin/bash
sleep 5
ip addr add 192.168.3.1/24 dev wlan0
ip link set wlan0 up
systemctl restart dnsmasq
```

Зробіть скрипт виконуваним:

```bash
sudo chmod +x /usr/local/bin/fix-wifi-ip.sh
```

Додайте автозапуск:

```bash
sudo nano /etc/rc.local
```

Додайте перед `exit 0`:

```bash
/usr/local/bin/fix-wifi-ip.sh &
```

---

## 5️⃣ Налаштування інтернету (NAT і Forwarding)

### Увімкнення IP-пересилання

```bash
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sysctl -p
```

### Налаштування iptables

```bash
sudo apt install iptables-persistent
sudo iptables -t nat -A POSTROUTING -o br0 -j MASQUERADE
sudo iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o br0 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

---

## 6️⃣ Оптимізація сервісів (Systemd)

```bash
sudo systemctl edit dnsmasq
```

Додайте:

```ini
[Unit]
After=hostapd.service

[Service]
Restart=on-failure
RestartSec=5
```

---

## ✅ Перевірка

```bash
# Перевірка IP-адреси wlan0
ip addr show wlan0  # Повинно бути 192.168.3.1

# Перевірка мосту
brctl show

# Перегляд логів dnsmasq
journalctl -u dnsmasq -f

# Перевірка hostapd
sudo systemctl status hostapd
```

---

## 📱 Підключення пристроїв

Після перезавантаження TV-приставки:

1. Знайдіть Wi-Fi мережу `MyArmbianAP` (або вашу назву)
2. Підключіться з паролем
3. Пристрої отримають IP адреси з діапазону 192.168.3.10-100
4. Інтернет працюватиме через NAT

---

**Останнє оновлення:** 2026-05-07
