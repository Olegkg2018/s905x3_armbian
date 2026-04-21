Инструкция по настройке AP (Точки доступа) на Armbian (S905X3)
Режим: Роутер (NAT), подсеть Wi-Fi: 192.168.3.x, подсеть LAN: 192.168.2.x.

1. Подготовка интерфейсов (NetworkManager)
Нам нужно объединить проводной порт в мост (для удобства самой приставки), но оставить Wi-Fi независимым.

Bash
# Создаем мост для проводной сети
sudo nmcli con add type bridge ifname br0 con-name br0
sudo nmcli con add type ethernet slave-type bridge master br0 ifname eth0 con-name eth0-br0
sudo nmcli con modify br0 ipv4.addresses 192.168.2.130/24 ipv4.gateway 192.168.2.1 ipv4.method manual
sudo nmcli con modify br0 ipv4.dns "8.8.8.8 8.8.4.4"
sudo nmcli con up br0

# Запрещаем NetworkManager трогать wlan0
sudo nano /etc/NetworkManager/NetworkManager.conf
Добавьте в секцию [keyfile]:

Ini, TOML
unmanaged-devices=interface-name:wlan0
2. Установка и настройка Hostapd
Bash
sudo apt install hostapd
sudo nano /etc/hostapd/hostapd.conf
Важный конфиг (БЕЗ строки bridge=br0):

Plaintext
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
3. Настройка DHCP (Dnsmasq)
Bash
sudo apt install dnsmasq
sudo nano /etc/dnsmasq.conf
Конфиг:

Plaintext
interface=wlan0
bind-dynamic
dhcp-range=192.168.3.10,192.168.3.100,12h
domain-needed
bogus-priv
4. Автоматизация настройки IP (Костыль для драйвера)
Так как драйвер не держит статику сам при загрузке, создаем скрипт:

Bash
sudo nano /usr/local/bin/fix-wifi-ip.sh
Содержимое:

Bash
#!/bin/bash
sleep 5
ip addr add 192.168.3.1/24 dev wlan0
ip link set wlan0 up
systemctl restart dnsmasq
Bash
sudo chmod +x /usr/local/bin/fix-wifi-ip.sh
Добавляем в автозагрузку перед exit 0:

Bash
sudo nano /etc/rc.local
# Вставить строку:
/usr/local/bin/fix-wifi-ip.sh &
5. Настройка интернета (NAT и Forwarding)
Чтобы на подключенных устройствах был интернет:

Включаем форвардинг навсегда:

Bash
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sysctl -p
Настраиваем Firewall:

Bash
sudo apt install iptables-persistent
sudo iptables -t nat -A POSTROUTING -o br0 -j MASQUERADE
sudo iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o br0 -j ACCEPT
# Сохраняем, чтобы не пропало после ребута
sudo iptables-save | sudo tee /etc/iptables/rules.v4
6. Оптимизация сервисов (Systemd)
Чтобы dnsmasq не падал, если Wi-Fi еще не готов:

Bash
sudo systemctl edit dnsmasq
Вставьте:

Ini, TOML
[Unit]
After=hostapd.service
[Service]
Restart=on-failure
RestartSec=5
Как проверять работоспособность:
ip addr show wlan0 — должен быть IP 192.168.3.1.

brctl show — в мосту br0 должен быть только eth0 (это нормально для этой схемы).

journalctl -u dnsmasq -f — должны идти DHCPACK.
