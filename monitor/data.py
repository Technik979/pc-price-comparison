# Demo products: {category: [(name, citilink_price, dns_price), ...]}
DEMO_PRODUCTS = {
    'Процессоры': [
        ('AMD Ryzen 5 5500',          9490,   9890),
        ('AMD Ryzen 5 5600X',        15990,  16490),
        ('AMD Ryzen 5 7600',         16990,  17490),
        ('AMD Ryzen 7 5800X3D',      27990,  28490),
        ('AMD Ryzen 7 7700X',        24990,  25490),
        ('AMD Ryzen 9 7950X',        53990,  54990),
        ('Intel Core i5-12400F',     14290,  14790),
        ('Intel Core i5-13400F',     14990,  15490),
        ('Intel Core i7-13700K',     31490,  32090),
        ('Intel Core i9-13900K',     49990,  51490),
    ],
    'Видеокарты': [
        ('AMD Radeon RX 6700 XT 12GB',      27990,  28490),
        ('AMD Radeon RX 7600 8GB',          28990,  29490),
        ('AMD Radeon RX 7900 GRE 16GB',     49990,  51490),
        ('AMD Radeon RX 7900 XTX 24GB',     79990,  81490),
        ('Intel Arc A770 16GB',             19990,  20490),
        ('NVIDIA GeForce RTX 3060 12GB',    22990,  23490),
        ('NVIDIA GeForce RTX 4060 8GB',     34490,  34990),
        ('NVIDIA GeForce RTX 4060 Ti 16GB', 44990,  45990),
        ('NVIDIA GeForce RTX 4070 12GB',    58990,  59990),
        ('NVIDIA GeForce RTX 4090 24GB',   149990, 152990),
    ],
    'Оперативная память': [
        ('Corsair Dominator DDR5 32GB 6000MHz',      11990, 12490),
        ('Corsair Vengeance DDR5 32GB 5600MHz',       8790,  8990),
        ('Crucial Pro DDR5 32GB 4800MHz',             7290,  7490),
        ('G.Skill Trident Z5 DDR5 64GB 6000MHz',    19490, 19990),
        ('HyperX FURY DDR4 32GB 3200MHz',            6490,  6790),
        ('Kingston FURY Beast DDR4 16GB 3200MHz',    3490,  3590),
        ('Kingston FURY Renegade DDR5 32GB 6400MHz',10990, 11490),
        ('Kingston ValueRAM DDR4 8GB 3200MHz',       1790,  1890),
        ('Patriot Viper Steel DDR4 16GB 4400MHz',    4990,  5290),
        ('Samsung DDR4 16GB 3200MHz (2x8GB)',         3290,  3490),
    ],
    'SSD': [
        ('ADATA XPG GAMMIX S70 2TB NVMe',   14990, 15490),
        ('Crucial MX500 500GB SATA',         4290,  4490),
        ('Crucial T700 2TB NVMe PCIe 5.0',  19990, 20490),
        ('Kingston KC3000 2TB NVMe',        12490, 12990),
        ('Kingston NV2 2TB NVMe',            7990,  8290),
        ('Samsung 870 EVO 1TB SATA',         8490,  8790),
        ('Samsung 870 QVO 2TB SATA',        11490, 11990),
        ('Samsung 980 Pro 2TB NVMe',        15990, 16490),
        ('Seagate FireCuda 530 2TB NVMe',   14490, 14990),
        ('Transcend 230S 1TB SATA',          5490,  5790),
        ('WD Black SN850X 1TB NVMe',         8290,  8590),
        ('WD Blue SN580 1TB NVMe',           5990,  6290),
    ],
    'Материнские платы': [
        ('ASRock B650M PG Riptide',            11990, 12490),
        ('ASRock X670E Taichi',                39990, 40990),
        ('ASUS PRIME Z790-P DDR5',             21990, 22490),
        ('ASUS ROG STRIX B550-F GAMING',       14990, 15490),
        ('ASUS TUF GAMING B650-PLUS WiFi',     17990, 18490),
        ('Gigabyte B450M DS3H',                 4990,  5290),
        ('Gigabyte X670E AORUS Master',        54990, 56490),
        ('MSI MAG B660 TOMAHAWK DDR4',         12490, 12990),
        ('MSI MAG X570S TORPEDO MAX',          19990, 20490),
        ('MSI PRO Z790-A DDR5 WiFi',           23990, 24490),
    ],
    'Ноутбуки': [
        ('Acer Aspire 3 A315 Ryzen 3 7320U 8GB',        29990,  30990),
        ('Acer Nitro 5 AN515 i7-12700H RTX 4060 16GB',  89990,  91490),
        ('Apple MacBook Air M2 8GB 256GB',               99990, 101990),
        ('Apple MacBook Pro 14 M3 Pro 18GB 512GB',      199990, 203990),
        ('ASUS ROG Strix G16 i9-13980HX RTX 4080',     189990, 192990),
        ('ASUS TUF Gaming F15 i5-12500H RTX 4060',      74990,  76490),
        ('ASUS VivoBook 15 i5-1235U 16GB 512GB',        54990,  55990),
        ('ASUS ZenBook 14 OLED i7-1360P 16GB',          84990,  86490),
        ('Dell Inspiron 15 3530 i5-1334U 16GB',         52990,  53990),
        ('HONOR MagicBook 14 i5-1240P 16GB 512GB',      44990,  45990),
        ('HP OMEN 16 Ryzen 9 7940HS RTX 4070',         129990, 131990),
        ('HP Pavilion 15 i5-1235U 8GB 512GB',           44990,  45990),
        ('Huawei MateBook D15 i5-1235U 16GB',           49990,  51490),
        ('Lenovo IdeaPad 1 15AMN7 Ryzen 5 8GB',         34990,  35990),
        ('Lenovo IdeaPad 3 Ryzen 5 5500U 16GB',         46990,  47990),
        ('Lenovo IdeaPad Gaming 3 Ryzen 5 7535HS RTX 2050', 54990, 56490),
        ('Lenovo Legion 5 Ryzen 7 7745HX RTX 4070',    109990, 111990),
        ('Lenovo ThinkPad E16 i5-1335U 16GB 512GB',     64990,  66490),
        ('Lenovo Yoga 9 14IRP8 i7-1360P 32GB',         119990, 121990),
        ('MSI Katana 15 i7-12650H RTX 4070 16GB',      119990, 121490),
        ('Samsung Galaxy Book3 360 i7-1360P 16GB',       89990,  91490),
        ('Xiaomi RedmiBook Pro 14 i7-13700H 16GB',       69990,  71490),
    ],
    'Сборки ПК': [
        ('Медиацентр: Intel N100 mini-PC 8GB 256GB',            14990,  15990),
        ('Офисная: Ryzen 3 4100 + 8GB DDR4 + SSD 256GB',       19990,  20990),
        ('Тихая: Ryzen 5 5600G + 16GB DDR4 + SSD 512GB',       29990,  31490),
        ('Бесшумная: Ryzen 5 PRO 4650G + 32GB DDR4 + SSD 1TB', 34990,  36490),
        ('Начальная: i3-12100F + GTX 1660S 16GB + SSD 512GB',  44990,  46490),
        ('1080p Средняя: i5-12400F + RX 7600 16GB DDR4',       64990,  66490),
        ('1080p Игровая: Ryzen 5 5600 + RTX 4060 16GB DDR4',   74990,  76990),
        ('1080p+: Ryzen 5 7600 + RTX 4060 Ti 16GB DDR5',       94990,  96990),
        ('1440p: i7-13700F + RTX 4070 32GB DDR5',             134990, 137490),
        ('1440p PRO: Ryzen 7 7700X + RTX 4070 Super 32GB',    154990, 157990),
        ('4K Игровая: i7-13700K + RTX 4080 32GB DDR5',        219990, 223990),
        ('Стрим: i9-13900K + RTX 4070 Ti + 64GB DDR5',        239990, 244990),
        ('Энтузиаст: Ryzen 9 7950X + RTX 4090 64GB DDR5',     389990, 395990),
        ('Рабочая станция: Ryzen 9 7950X + 128GB ECC + 4TB',  299990, 305990),
    ],
    'Кабели и провода': [
        ('DisplayPort 1.4 1.8м Telecom',                 890,    990),
        ('HDMI 2.0 угловой 90 1.5м Buro',               490,    590),
        ('Кабель HDMI 2.1 2м Buro',                      590,    690),
        ('Кабель Molex-SATA 15см Akasa',                 290,    350),
        ('Кабель SATA III 50см Cablexpert',              190,    240),
        ('Кабель питания ATX 24pin 30см Akasa',          590,    650),
        ('Кабель RJ45 Cat7 5м экранированный Telecom',   790,    890),
        ('Mini-DisplayPort HDMI 1.8м Buro',              890,    990),
        ('Патч-корд UTP Cat6 3м Cablexpert',             290,    350),
        ('Thunderbolt 4 0.8м 40Gbps Orico',             2990,   3290),
        ('USB 3.0 A-B 1.8м принтерный Gembird',          390,    450),
        ('USB-C USB-C 1м 100W Baseus',                  1290,   1390),
    ],
}

LAPTOP_SPECS = {
    'Acer Aspire 3 A315 Ryzen 3 7320U 8GB':
        '15.6" FHD IPS · AMD Ryzen 3 7320U · 8GB DDR5 · 256GB NVMe · AMD Radeon 610M',
    'Acer Nitro 5 AN515 i7-12700H RTX 4060 16GB':
        '15.6" FHD IPS 144Hz · Intel Core i7-12700H · 16GB DDR4 · 512GB NVMe · RTX 4060 8GB',
    'Apple MacBook Air M2 8GB 256GB':
        '13.6" Liquid Retina 2560x1664 · Apple M2 · 8GB · 256GB SSD · GPU 8-core',
    'Apple MacBook Pro 14 M3 Pro 18GB 512GB':
        '14.2" Liquid XDR 3024x1964 ProMotion · Apple M3 Pro · 18GB · 512GB SSD · GPU 18-core',
    'ASUS ROG Strix G16 i9-13980HX RTX 4080':
        '16" QHD+ IPS 240Hz · Intel Core i9-13980HX · 32GB DDR5 · 1TB NVMe · RTX 4080 12GB',
    'ASUS TUF Gaming F15 i5-12500H RTX 4060':
        '15.6" FHD IPS 144Hz · Intel Core i5-12500H · 16GB DDR4 · 512GB NVMe · RTX 4060 8GB',
    'ASUS VivoBook 15 i5-1235U 16GB 512GB':
        '15.6" FHD IPS · Intel Core i5-1235U · 16GB DDR4 · 512GB NVMe · Intel Iris Xe',
    'ASUS ZenBook 14 OLED i7-1360P 16GB':
        '14" 2.8K OLED 90Hz · Intel Core i7-1360P · 16GB DDR5 · 1TB NVMe · Intel Iris Xe',
    'Dell Inspiron 15 3530 i5-1334U 16GB':
        '15.6" FHD IPS · Intel Core i5-1334U · 16GB DDR4 · 512GB NVMe · Intel UHD',
    'HONOR MagicBook 14 i5-1240P 16GB 512GB':
        '14" IPS 1920x1200 · Intel Core i5-1240P · 16GB DDR4 · 512GB NVMe · Intel Iris Xe',
    'HP OMEN 16 Ryzen 9 7940HS RTX 4070':
        '16.1" FHD IPS 165Hz · AMD Ryzen 9 7940HS · 32GB DDR5 · 1TB NVMe · RTX 4070 8GB',
    'HP Pavilion 15 i5-1235U 8GB 512GB':
        '15.6" FHD IPS · Intel Core i5-1235U · 8GB DDR4 · 512GB NVMe · Intel Iris Xe',
    'Huawei MateBook D15 i5-1235U 16GB':
        '15.6" FHD IPS · Intel Core i5-1235U · 16GB DDR4 · 512GB NVMe · Intel Iris Xe',
    'Lenovo IdeaPad 1 15AMN7 Ryzen 5 8GB':
        '15.6" FHD IPS · AMD Ryzen 5 7520U · 8GB DDR5 · 256GB NVMe · AMD Radeon 610M',
    'Lenovo IdeaPad 3 Ryzen 5 5500U 16GB':
        '15.6" FHD IPS · AMD Ryzen 5 5500U · 16GB DDR4 · 512GB NVMe · AMD Radeon Vega 7',
    'Lenovo IdeaPad Gaming 3 Ryzen 5 7535HS RTX 2050':
        '15.6" FHD IPS 120Hz · AMD Ryzen 5 7535HS · 16GB DDR5 · 512GB NVMe · RTX 2050 4GB',
    'Lenovo Legion 5 Ryzen 7 7745HX RTX 4070':
        '15.6" FHD IPS 165Hz · AMD Ryzen 7 7745HX · 32GB DDR5 · 1TB NVMe · RTX 4070 8GB',
    'Lenovo ThinkPad E16 i5-1335U 16GB 512GB':
        '16" WUXGA IPS · Intel Core i5-1335U · 16GB DDR4 · 512GB NVMe · Intel Iris Xe',
    'Lenovo Yoga 9 14IRP8 i7-1360P 32GB':
        '14" 2.8K OLED 90Hz Touch · Intel Core i7-1360P · 32GB DDR5 · 1TB NVMe · Intel Iris Xe',
    'MSI Katana 15 i7-12650H RTX 4070 16GB':
        '15.6" FHD IPS 144Hz · Intel Core i7-12650H · 16GB DDR4 · 1TB NVMe · RTX 4070 8GB',
    'Samsung Galaxy Book3 360 i7-1360P 16GB':
        '15.6" FHD AMOLED Touch · Intel Core i7-1360P · 16GB DDR4 · 512GB NVMe · Intel Iris Xe',
    'Xiaomi RedmiBook Pro 14 i7-13700H 16GB':
        '14" 2.8K OLED 90Hz · Intel Core i7-13700H · 16GB DDR5 · 512GB NVMe · Intel Arc',
}

CATEGORY_ICONS = {
    'Процессоры':         '⚡',
    'Видеокарты':         '🎮',
    'Оперативная память': '💾',
    'SSD':                '💿',
    'Материнские платы':  '🔧',
    'Ноутбуки':           '💻',
    'Сборки ПК':          '🖥️',
    'Кабели и провода':   '🔌',
}
