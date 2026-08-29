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

# Найдены разведкой 29.08 11:34, каждый проверен curl-ом: точный парт-номер в HTML,
# цена в schema.org (itemprop="price" или JSON-LD Offer) — читаются тем же парсером.
SSD_EXTRA = [
    {"shop": "network-it.ru", "sku": SKU,
     "url": "https://network-it.ru/products/samsung-mzilg7t6hbla-00a07"},
    {"shop": "shop.nag.ru", "sku": SKU,
     "url": "https://shop.nag.ru/catalog/31464.komplektuyuschie-dlya-serverov-i-shd/"
            "33568.servernye-ssd/84850.mzilg7t6hbla-00a07"},
    {"shop": "gesc.ru", "sku": SKU,
     "url": "https://gesc.ru/catalog/servernoe-oborudovanie/servernye-ssd-/ssd-samsung/"
            "nakopitel_ssd_samsung_pm1653_7_68tb_mzilg7t6hbla_00a07/"},
    {"shop": "shop.nav-it.ru", "sku": SKU,
     "url": "https://shop.nav-it.ru/catalogue/servernye_zhestkie_diski_ssd/"
            "samsung_ssd_pm1653_7680gb_2_5_15mm_sas_24gb_s_3d_tlc_mzilg7t6hbla_00a07/"},
    {"shop": "brigo.ru", "sku": SKU,
     "url": "https://brigo.ru/nakopitel-ssd-7-68tb-sas-samsung-pm1653-"
            "mzilg7t6hbla-00a07-318252.html"},
    {"shop": "tehpos.ru", "sku": SKU,
     "url": "https://tehpos.ru/novomoskovsk/samsung-pm1653-7680gb-mzilg7t6hbla-00a07.html"},
    {"shop": "netshopping.ru", "sku": SKU,
     "url": "https://netshopping.ru/product/tverdotelnyy-nakopitel-samsung-ssd-pm1653-"
            "7680gb-2-5-15mm-sas-24gb-s-3d-tlc-r-w-4200-up-380/"},
]

ALL_SOURCES = SSD_CASE + SSD_EXTRA
