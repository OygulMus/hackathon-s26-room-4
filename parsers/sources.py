"""Список источников комнаты.

Демо-кейс — SSD Samsung PM1653 7.68TB, парт-номер MZILG7T6HBLA-00A07,
пять магазинов. Принесён заказчиком Алексеем, проверен и смержен в PR #9.
Три из пяти закрыты от робота — они остаются в списке намеренно: инструмент
обязан показывать «источник недоступен», а не молча сокращать картину.
"""

SKU = "MZILG7T6HBLA-00A07"

SSD_CASE = [
    {"shop": "xcom-shop.ru", "sku": SKU,
     "url": "https://www.xcom-shop.ru/samsung_mzilg7t6hbla-00a07_1030281.html"},
    {"shop": "regard.ru", "sku": SKU,
     "url": "https://www.regard.ru/product/461931/"
            "nakopitel-ssd-768tb-sas-samsung-pm1653-mzilg7t6hbla-00a07"},
    {"shop": "onlinetrade.ru", "sku": SKU,
     "url": "https://www.onlinetrade.ru/catalogue/servernye_ssd-c8709/samsung/"
            "nakopitel_ssd_samsung_enterprise_ssd_pm1653_7.68_tb_2.5_sas_24gb_s"
            "_4200_mb_s_3700_mb_s_128_layer_v_nand_mzilg7t6hbla_00a07-3655338.html"},
    {"shop": "kns.ru", "sku": SKU,
     "url": "https://www.kns.ru/product/"
            "ssd-disk-samsung-pm1653-7-68tb-mzilg7t6hbla-00a07/"},
    {"shop": "citilink.ru", "sku": SKU,
     "url": "https://www.citilink.ru/product/"
            "nakopitel-ssd-samsung-1-sas-2-5-mzilg7t6hbla-00a07-1948438/"},
]
