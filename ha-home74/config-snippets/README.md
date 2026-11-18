Фрагменты `configuration.yaml` (template-сенсоры), на которые опирается дашборд:

- `sensor.grid_voltage_effective` — напряжение сети: датчик автомата `sensor.ji_liang_duan_lu_qi_voltage`, запасной — счётчик Atorch.
- `sensor.grid_power_clamps` — мощность из сети по Zigbee-клещам (TS060) = −(A+B), поправка +60 Вт; запасной — `sensor.moshchnost_iz_seti`.
- `binary_sensor.outage_soon` — «в ближайшие 3 часа плановое отключение» по сенсорам ЯСНО.

Подставьте свои entity_id. Файл `template-sensors.yaml` — это выдержка (блок `sensor:` и `binary_sensor:` из списка `template:`), а не готовый конфиг.
