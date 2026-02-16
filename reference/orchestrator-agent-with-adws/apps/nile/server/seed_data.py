"""Seed database with product data from metadata files."""
import asyncio

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.config import DATABASE_URL
from src.database import Base
from src.models import Product, Review


async def seed_products():
    """Seed products from metadata JSON files."""
    # Create engine and tables
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    products_data = [
        # === KEYBOARDS (10) ===
        {
            "name": "Keychron Q1 Pro",
            "description": "Premium 75% wireless mechanical keyboard with full aluminum body, hot-swappable switches, QMK/VIA support, and 1000Hz polling rate.",
            "price": 199.0,
            "category": "Keyboards",
            "brand": "Keychron",
            "rating": 4.7,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/keychron_q1_pro.webp",
            "reviews": [
                {"review_text": "The typing experience is phenomenal.", "rating": 5, "reviewer_name": "MechKeyFan", "review_date": "2024-11-10"},
                {"review_text": "Hot-swap feature is amazing!", "rating": 5, "reviewer_name": "KeyboardEnthusiast", "review_date": "2024-10-18"}
            ]
        },
        {
            "name": "Logitech G Pro X 60",
            "description": "60% wireless gaming keyboard with LIGHTSPEED technology, GX optical switches, and RGB LIGHTSYNC.",
            "price": 179.0,
            "category": "Keyboards",
            "brand": "Logitech",
            "rating": 4.6,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/logitech_g_pro_x_60.webp",
            "reviews": [
                {"review_text": "Compact and responsive for esports.", "rating": 5, "reviewer_name": "ProGamer", "review_date": "2024-10-20"}
            ]
        },
        {
            "name": "Razer Huntsman V3 Pro",
            "description": "Full-size analog optical keyboard with adjustable actuation, magnetic wrist rest, and Razer Chroma RGB.",
            "price": 249.0,
            "category": "Keyboards",
            "brand": "Razer",
            "rating": 4.8,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/razer_huntsman_v3_pro.webp",
            "reviews": [
                {"review_text": "Analog actuation is a game changer.", "rating": 5, "reviewer_name": "KeyboardNinja", "review_date": "2024-11-01"}
            ]
        },
        {
            "name": "HHKB Hybrid Type-S",
            "description": "Premium 60% keyboard with Topre electrostatic capacitive switches, Bluetooth, and USB-C connectivity.",
            "price": 369.0,
            "category": "Keyboards",
            "brand": "PFU",
            "rating": 4.9,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/hhkb_hybrid_type_s.webp",
            "reviews": [
                {"review_text": "The Topre feel is unmatched.", "rating": 5, "reviewer_name": "TypeEnthusiast", "review_date": "2024-09-15"}
            ]
        },
        {
            "name": "Cipher Biometric Keyboard",
            "description": "Secure keyboard with built-in fingerprint reader, AES-256 encryption, and programmable keys.",
            "price": 299.0,
            "category": "Keyboards",
            "brand": "Cipher",
            "rating": 4.5,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/cipher_biometric_keyboard.webp",
            "reviews": [
                {"review_text": "Security and convenience combined.", "rating": 4, "reviewer_name": "SecurityPro", "review_date": "2024-10-05"}
            ]
        },
        {
            "name": "Aethon Apex 75",
            "description": "Custom 75% keyboard with gasket mount, hot-swap PCB, and premium PBT keycaps.",
            "price": 189.0,
            "category": "Keyboards",
            "brand": "Aethon",
            "rating": 4.7,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/aethon_apex_75.webp",
            "reviews": [
                {"review_text": "Great build quality for the price.", "rating": 5, "reviewer_name": "MechBuilder", "review_date": "2024-10-28"}
            ]
        },
        {
            "name": "Aethon Stealth 60",
            "description": "Compact 60% keyboard with silent switches, black anodized aluminum case, and wireless connectivity.",
            "price": 159.0,
            "category": "Keyboards",
            "brand": "Aethon",
            "rating": 4.6,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/aethon_stealth_60.webp",
            "reviews": [
                {"review_text": "Perfect for quiet office environments.", "rating": 5, "reviewer_name": "QuietTyper", "review_date": "2024-09-20"}
            ]
        },

        # === MICE (8) ===
        {
            "name": "Logitech MX Master 3S",
            "description": "Premium wireless mouse with 8K DPI sensor, quiet clicks, and MagSpeed electromagnetic scrolling.",
            "price": 99.0,
            "category": "Mice",
            "brand": "Logitech",
            "rating": 4.8,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/logitech_mx_master_3s.webp",
            "reviews": [
                {"review_text": "Best mouse I've ever used for productivity.", "rating": 5, "reviewer_name": "DevPro", "review_date": "2024-11-05"}
            ]
        },
        {
            "name": "Logitech MX Anywhere 3S",
            "description": "Compact wireless mouse with 8K DPI, quiet clicks, and works on any surface including glass.",
            "price": 79.0,
            "category": "Mice",
            "brand": "Logitech",
            "rating": 4.7,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/logitech_mx_anywhere_3s.webp",
            "reviews": [
                {"review_text": "Perfect travel companion.", "rating": 5, "reviewer_name": "TravelWorker", "review_date": "2024-10-15"}
            ]
        },
        {
            "name": "Logitech G Pro X Superlight 2",
            "description": "Ultra-lightweight wireless gaming mouse at 60g with HERO 2 sensor and LIGHTSPEED technology.",
            "price": 159.0,
            "category": "Mice",
            "brand": "Logitech",
            "rating": 4.9,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/logitech_g_pro_x_superlight_2.webp",
            "reviews": [
                {"review_text": "Esports perfection.", "rating": 5, "reviewer_name": "FPSChamp", "review_date": "2024-11-02"}
            ]
        },
        {
            "name": "Keychron M6 Mouse",
            "description": "Wireless ergonomic mouse with 26K DPI sensor, 1000Hz polling, and 79-hour battery life.",
            "price": 69.0,
            "category": "Mice",
            "brand": "Keychron",
            "rating": 4.5,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/keychron_m6_mouse.webp",
            "reviews": [
                {"review_text": "Great value for wireless.", "rating": 4, "reviewer_name": "BudgetGamer", "review_date": "2024-09-25"}
            ]
        },
        {
            "name": "Razer DeathAdder V3 Pro",
            "description": "Wireless ergonomic gaming mouse with Focus Pro 30K sensor and 90-hour battery life.",
            "price": 149.0,
            "category": "Mice",
            "brand": "Razer",
            "rating": 4.8,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/razer_deathadder_v3_pro.webp",
            "reviews": [
                {"review_text": "Legendary shape, wireless freedom.", "rating": 5, "reviewer_name": "DAFan", "review_date": "2024-10-10"}
            ]
        },
        {
            "name": "Finalmouse UltralightX",
            "description": "Ultra-lightweight gaming mouse at 29g with magnesium shell and Finalsensor technology.",
            "price": 189.0,
            "category": "Mice",
            "brand": "Finalmouse",
            "rating": 4.6,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/finalmouse_ultralightx.webp",
            "reviews": [
                {"review_text": "Incredibly light, takes getting used to.", "rating": 4, "reviewer_name": "LightweightFan", "review_date": "2024-10-22"}
            ]
        },

        # === AUDIO (10) ===
        {
            "name": "Sony WH-1000XM5",
            "description": "Industry-leading noise canceling wireless headphones with exceptional sound quality and 30-hour battery life.",
            "price": 349.0,
            "category": "Audio",
            "brand": "Sony",
            "rating": 4.9,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/sony_wh-1000xm5.webp",
            "reviews": [
                {"review_text": "Noise cancellation is unreal.", "rating": 5, "reviewer_name": "AudioPhile", "review_date": "2024-10-20"}
            ]
        },
        {
            "name": "Bose QuietComfort Ultra",
            "description": "Premium headphones with immersive audio, world-class noise cancellation, and spatial audio.",
            "price": 429.0,
            "category": "Audio",
            "brand": "Bose",
            "rating": 4.8,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/bose_quietcomfort_ultra.webp",
            "reviews": [
                {"review_text": "Bose at their finest.", "rating": 5, "reviewer_name": "BoseFan", "review_date": "2024-11-05"}
            ]
        },
        {
            "name": "SteelSeries Arctis Nova Pro",
            "description": "Premium wireless gaming headset with 360° spatial audio, active noise cancellation, and hot-swap batteries.",
            "price": 349.0,
            "category": "Audio",
            "brand": "SteelSeries",
            "rating": 4.7,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/steelseries_arctis_nova_pro.webp",
            "reviews": [
                {"review_text": "Best gaming audio experience.", "rating": 5, "reviewer_name": "AudioGamer", "review_date": "2024-10-08"}
            ]
        },
        {
            "name": "Blue Yeti X Microphone",
            "description": "Professional USB condenser microphone with 4 pickup patterns and Blue VO!CE software.",
            "price": 169.0,
            "category": "Audio",
            "brand": "Blue",
            "rating": 4.6,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/blue_yeti_x_microphone.webp",
            "reviews": [
                {"review_text": "Studio quality for podcasting.", "rating": 5, "reviewer_name": "PodcasterPro", "review_date": "2024-10-01"}
            ]
        },
        {
            "name": "Rode PodMic USB",
            "description": "Dynamic USB microphone optimized for podcasting with internal pop filter and rich broadcast sound.",
            "price": 199.0,
            "category": "Audio",
            "brand": "Rode",
            "rating": 4.7,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/rode_podmic_usb.webp",
            "reviews": [
                {"review_text": "Broadcast quality at home.", "rating": 5, "reviewer_name": "VoiceoverArtist", "review_date": "2024-10-15"}
            ]
        },
        {
            "name": "Elgato Wave DX",
            "description": "Dynamic XLR microphone with tight polar pattern, internal shock mount, and broadcast-ready sound.",
            "price": 149.0,
            "category": "Audio",
            "brand": "Elgato",
            "rating": 4.6,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/elgato_wave_dx.webp",
            "reviews": [
                {"review_text": "Clean audio without background noise.", "rating": 5, "reviewer_name": "Streamer101", "review_date": "2024-09-28"}
            ]
        },

        # === LAPTOPS & TABLETS (8) ===
        {
            "name": "Apple MacBook Pro 14",
            "description": "M3 Pro chip, 14-inch Liquid Retina XDR display, 18GB unified memory, 512GB SSD.",
            "price": 1999.0,
            "category": "Laptops",
            "brand": "Apple",
            "rating": 4.9,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/apple_macbook_pro_14.webp",
            "reviews": [
                {"review_text": "Incredible performance for development.", "rating": 5, "reviewer_name": "MacDevPro", "review_date": "2024-11-01"}
            ]
        },
        {
            "name": "Razer Blade 18 2025",
            "description": "18-inch gaming laptop with RTX 4090, Intel Core i9, 4K 200Hz display, and per-key RGB.",
            "price": 4299.0,
            "category": "Laptops",
            "brand": "Razer",
            "rating": 4.7,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/razer_blade_18_2025.webp",
            "reviews": [
                {"review_text": "Desktop replacement beast.", "rating": 5, "reviewer_name": "LaptopGamer", "review_date": "2024-10-30"}
            ]
        },
        {
            "name": "Apple iPad Pro 13",
            "description": "M4 chip, 13-inch Ultra Retina XDR display, 256GB storage, and Apple Pencil Pro support.",
            "price": 1299.0,
            "category": "Tablets",
            "brand": "Apple",
            "rating": 4.8,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/apple_ipad_pro_13.webp",
            "reviews": [
                {"review_text": "More powerful than most laptops.", "rating": 5, "reviewer_name": "iPadArtist", "review_date": "2024-11-08"}
            ]
        },
        {
            "name": "Samsung Galaxy Tab S10 Ultra",
            "description": "14.6-inch AMOLED display, Snapdragon 8 Gen 3, S Pen included, and DeX desktop mode.",
            "price": 1199.0,
            "category": "Tablets",
            "brand": "Samsung",
            "rating": 4.6,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/samsung_galaxy_tab_s10_ultra.webp",
            "reviews": [
                {"review_text": "Android tablet done right.", "rating": 5, "reviewer_name": "TabletUser", "review_date": "2024-10-18"}
            ]
        },
        {
            "name": "reMarkable 3",
            "description": "E-ink writing tablet with paper-like feel, Type Folio keyboard, and cloud sync.",
            "price": 599.0,
            "category": "Tablets",
            "brand": "reMarkable",
            "rating": 4.5,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/remarkable_3.webp",
            "reviews": [
                {"review_text": "Best digital notebook experience.", "rating": 5, "reviewer_name": "NoteTaker", "review_date": "2024-09-10"}
            ]
        },
        {
            "name": "Apple Pencil Pro",
            "description": "Advanced stylus with squeeze gesture, barrel roll, and haptic feedback for iPad Pro.",
            "price": 129.0,
            "category": "Accessories",
            "brand": "Apple",
            "rating": 4.8,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/apple_pencil_pro.webp",
            "reviews": [
                {"review_text": "Essential for iPad artists.", "rating": 5, "reviewer_name": "DigitalArtist", "review_date": "2024-10-25"}
            ]
        },

        # === MONITORS (8) ===
        {
            "name": "LG UltraFine 27 4K Monitor",
            "description": "27-inch 4K UHD IPS display with USB-C connectivity, 60W power delivery, and color accuracy.",
            "price": 699.0,
            "category": "Monitors",
            "brand": "LG",
            "rating": 4.6,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/lg_ultrafine_27_4k_monitor.webp",
            "reviews": [
                {"review_text": "Color accuracy is fantastic for design work.", "rating": 5, "reviewer_name": "Designer101", "review_date": "2024-09-15"}
            ]
        },
        {
            "name": "Apple Studio Display",
            "description": "27-inch 5K Retina display with A13 Bionic chip, Center Stage camera, and studio-quality mics.",
            "price": 1599.0,
            "category": "Monitors",
            "brand": "Apple",
            "rating": 4.6,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/apple_studio_display.webp",
            "reviews": [
                {"review_text": "Beautiful display, perfect for Mac.", "rating": 5, "reviewer_name": "AppleEcosystem", "review_date": "2024-09-12"}
            ]
        },

        # === DESKTOPS & WORKSTATIONS (6) ===
        {
            "name": "Apple Mac Studio M2 Ultra",
            "description": "M2 Ultra chip, 64GB unified memory, 1TB SSD. Incredible performance for creative professionals.",
            "price": 3999.0,
            "category": "Desktops",
            "brand": "Apple",
            "rating": 4.9,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/apple_mac_studio_m2_ultra.webp",
            "reviews": [
                {"review_text": "Best machine I've ever owned.", "rating": 5, "reviewer_name": "VideoEditor", "review_date": "2024-11-08"}
            ]
        },
        {
            "name": "NVIDIA DGX Spark Pro",
            "description": "AI development workstation with RTX 6000 Ada GPU, 128GB RAM, and 4TB NVMe storage.",
            "price": 14999.0,
            "category": "Workstations",
            "brand": "NVIDIA",
            "rating": 4.9,
            "shipping_speed": "14-day",
            "image_file_path": "/images/products/nvidia_dgx_spark_pro.webp",
            "reviews": [
                {"review_text": "AI training powerhouse.", "rating": 5, "reviewer_name": "MLEngineer", "review_date": "2024-10-05"}
            ]
        },
        {
            "name": "NVIDIA DGX Spark Max",
            "description": "Ultimate AI workstation with dual RTX 6000 Ada GPUs, 256GB RAM, and 8TB NVMe RAID.",
            "price": 29999.0,
            "category": "Workstations",
            "brand": "NVIDIA",
            "rating": 5.0,
            "shipping_speed": "21-day",
            "image_file_path": "/images/products/nvidia_dgx_spark_max.webp",
            "reviews": [
                {"review_text": "Enterprise AI in a box.", "rating": 5, "reviewer_name": "AIResearcher", "review_date": "2024-09-28"}
            ]
        },
        {
            "name": "NVIDIA DGX Spark Ultra",
            "description": "Research-grade AI system with 4x RTX 6000 Ada GPUs, 512GB RAM, and 16TB NVMe storage.",
            "price": 59999.0,
            "category": "Workstations",
            "brand": "NVIDIA",
            "rating": 5.0,
            "shipping_speed": "30-day",
            "image_file_path": "/images/products/nvidia_dgx_spark_ultra.webp",
            "reviews": [
                {"review_text": "The future of AI research.", "rating": 5, "reviewer_name": "DeepLearningLab", "review_date": "2024-10-12"}
            ]
        },

        # === STORAGE (8) ===
        {
            "name": "Samsung 990 Pro 2TB",
            "description": "PCIe 4.0 NVMe SSD with up to 7,450MB/s read speeds and advanced thermal control.",
            "price": 179.0,
            "category": "Storage",
            "brand": "Samsung",
            "rating": 4.8,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/samsung_990_pro_2tb.webp",
            "reviews": [
                {"review_text": "Blazing fast speeds!", "rating": 5, "reviewer_name": "StorageGeek", "review_date": "2024-10-10"}
            ]
        },
        {
            "name": "Samsung 990 EVO 4TB",
            "description": "PCIe 5.0 NVMe SSD with up to 10,000MB/s read speeds and intelligent TurboWrite.",
            "price": 349.0,
            "category": "Storage",
            "brand": "Samsung",
            "rating": 4.9,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/samsung_990_evo_4tb.webp",
            "reviews": [
                {"review_text": "PCIe 5.0 speed is incredible.", "rating": 5, "reviewer_name": "SpeedFreak", "review_date": "2024-11-01"}
            ]
        },
        {
            "name": "WD Black P10 4TB",
            "description": "Portable gaming drive with 4TB capacity, USB 3.2 Gen 1, and durable metal enclosure.",
            "price": 119.0,
            "category": "Storage",
            "brand": "Western Digital",
            "rating": 4.5,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/wd_black_p10_4tb.webp",
            "reviews": [
                {"review_text": "Perfect for game storage.", "rating": 4, "reviewer_name": "GameCollector", "review_date": "2024-09-10"}
            ]
        },
        {
            "name": "WD Black SN850X 2TB",
            "description": "PCIe 4.0 gaming SSD with up to 7,300MB/s read speeds and Game Mode 2.0.",
            "price": 149.0,
            "category": "Storage",
            "brand": "Western Digital",
            "rating": 4.7,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/wd_black_sn850x_2tb.webp",
            "reviews": [
                {"review_text": "Game loads are instant.", "rating": 5, "reviewer_name": "ConsoleGamer", "review_date": "2024-10-08"}
            ]
        },
        {
            "name": "Sabrent Rocket 5 2TB",
            "description": "PCIe 5.0 NVMe SSD with up to 14,000MB/s read speeds and advanced heatsink.",
            "price": 399.0,
            "category": "Storage",
            "brand": "Sabrent",
            "rating": 4.8,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/sabrent_rocket_5_2tb.webp",
            "reviews": [
                {"review_text": "Fastest consumer SSD available.", "rating": 5, "reviewer_name": "TechReviewer", "review_date": "2024-10-28"}
            ]
        },
        {
            "name": "Synology DS923+ NAS",
            "description": "4-bay NAS with AMD Ryzen CPU, 4GB DDR4, dual M.2 NVMe cache slots, and 10GbE expansion.",
            "price": 599.0,
            "category": "Storage",
            "brand": "Synology",
            "rating": 4.8,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/synology_ds923_nas.webp",
            "reviews": [
                {"review_text": "Best home server solution.", "rating": 5, "reviewer_name": "HomeLab", "review_date": "2024-09-20"}
            ]
        },
        {
            "name": "Synology DS1522+ NAS",
            "description": "5-bay NAS with AMD Ryzen CPU, 8GB DDR4, SSD cache, and expandable to 15 drives.",
            "price": 749.0,
            "category": "Storage",
            "brand": "Synology",
            "rating": 4.9,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/synology_ds1522_nas.webp",
            "reviews": [
                {"review_text": "Enterprise features at prosumer price.", "rating": 5, "reviewer_name": "DataHoarder", "review_date": "2024-10-15"}
            ]
        },
        {
            "name": "TerraMaster F4-424 Pro",
            "description": "4-bay NAS with Intel N95 CPU, 8GB DDR5, dual 2.5GbE, and hardware transcoding.",
            "price": 469.0,
            "category": "Storage",
            "brand": "TerraMaster",
            "rating": 4.5,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/terramaster_f4_424_pro.webp",
            "reviews": [
                {"review_text": "Great value NAS solution.", "rating": 4, "reviewer_name": "BudgetNAS", "review_date": "2024-09-05"}
            ]
        },

        # === COMPONENTS (12) ===
        {
            "name": "NVIDIA RTX 4070 Super",
            "description": "Graphics card with 12GB GDDR6X, DLSS 3, and ray tracing for gaming and content creation.",
            "price": 599.0,
            "category": "Components",
            "brand": "NVIDIA",
            "rating": 4.8,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/nvidia_rtx_4070_super.webp",
            "reviews": [
                {"review_text": "Great performance at 1440p.", "rating": 5, "reviewer_name": "PCBuilder", "review_date": "2024-10-18"}
            ]
        },
        {
            "name": "NVIDIA RTX 4060 Ti 16GB",
            "description": "Graphics card with 16GB GDDR6, DLSS 3, and excellent 1080p ray tracing performance.",
            "price": 449.0,
            "category": "Components",
            "brand": "NVIDIA",
            "rating": 4.6,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/nvidia_rtx_4060_ti_16gb.webp",
            "reviews": [
                {"review_text": "Best value mid-range card.", "rating": 5, "reviewer_name": "BudgetBuilder", "review_date": "2024-10-02"}
            ]
        },
        {
            "name": "NVIDIA RTX 4080 Super",
            "description": "High-end graphics card with 16GB GDDR6X, DLSS 3, and 4K gaming performance.",
            "price": 999.0,
            "category": "Components",
            "brand": "NVIDIA",
            "rating": 4.8,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/nvidia_rtx_4080_super.webp",
            "reviews": [
                {"review_text": "4K gaming finally achievable.", "rating": 5, "reviewer_name": "4KGamer", "review_date": "2024-10-25"}
            ]
        },
        {
            "name": "NVIDIA RTX 4090",
            "description": "Flagship graphics card with 24GB GDDR6X, ultimate ray tracing, and content creation performance.",
            "price": 1599.0,
            "category": "Components",
            "brand": "NVIDIA",
            "rating": 4.9,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/nvidia_rtx_4090.webp",
            "reviews": [
                {"review_text": "The king of GPUs.", "rating": 5, "reviewer_name": "Enthusiast", "review_date": "2024-09-30"}
            ]
        },
        {
            "name": "NVIDIA RTX 5060",
            "description": "Next-gen graphics card with 8GB GDDR7, Blackwell architecture, and enhanced DLSS 4.",
            "price": 329.0,
            "category": "Components",
            "brand": "NVIDIA",
            "rating": 4.7,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/nvidia_rtx_5060.webp",
            "reviews": [
                {"review_text": "Great entry-level next-gen card.", "rating": 5, "reviewer_name": "FirstBuilder", "review_date": "2024-11-05"}
            ]
        },
        {
            "name": "NVIDIA RTX 5070",
            "description": "Next-gen graphics card with 12GB GDDR7, Blackwell architecture, and RTX 4090-level performance.",
            "price": 549.0,
            "category": "Components",
            "brand": "NVIDIA",
            "rating": 4.9,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/nvidia_rtx_5070.webp",
            "reviews": [
                {"review_text": "4090 performance at half the price!", "rating": 5, "reviewer_name": "ValueSeeker", "review_date": "2024-11-08"}
            ]
        },
        {
            "name": "NVIDIA RTX 5070 Ti",
            "description": "Next-gen graphics card with 16GB GDDR7, Blackwell architecture, and enhanced ray tracing.",
            "price": 749.0,
            "category": "Components",
            "brand": "NVIDIA",
            "rating": 4.8,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/nvidia_rtx_5070_ti.webp",
            "reviews": [
                {"review_text": "Sweet spot for next-gen gaming.", "rating": 5, "reviewer_name": "GamingEnthusiast", "review_date": "2024-11-10"}
            ]
        },
        {
            "name": "Corsair Vengeance 32GB DDR5",
            "description": "DDR5 RAM kit (2x16GB) at 5600MHz with Intel XMP 3.0 support and aluminum heat spreader.",
            "price": 119.0,
            "category": "Components",
            "brand": "Corsair",
            "rating": 4.7,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/corsair_vengeance_32gb_ddr5.webp",
            "reviews": [
                {"review_text": "Fast and reliable RAM.", "rating": 5, "reviewer_name": "MemoryUpgrader", "review_date": "2024-10-22"}
            ]
        },
        {
            "name": "Corsair Dominator Platinum 128GB DDR5",
            "description": "Premium DDR5 RAM kit (4x32GB) at 6400MHz with iCUE RGB and DHX cooling.",
            "price": 599.0,
            "category": "Components",
            "brand": "Corsair",
            "rating": 4.9,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/corsair_dominator_platinum_128gb.webp",
            "reviews": [
                {"review_text": "The ultimate workstation RAM.", "rating": 5, "reviewer_name": "ContentCreator", "review_date": "2024-10-18"}
            ]
        },
        {
            "name": "Noctua NH-D15 Cooler",
            "description": "Premium dual-tower CPU cooler with two NF-A15 fans, near-silent operation.",
            "price": 109.0,
            "category": "Components",
            "brand": "Noctua",
            "rating": 4.9,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/noctua_nh_d15_cooler.webp",
            "reviews": [
                {"review_text": "Silent and incredibly effective.", "rating": 5, "reviewer_name": "SilentPCBuilder", "review_date": "2024-08-28"}
            ]
        },
        {
            "name": "Corsair H150i Elite LCD",
            "description": "360mm AIO liquid cooler with customizable LCD display, RGB pump head, and ML120 fans.",
            "price": 289.0,
            "category": "Components",
            "brand": "Corsair",
            "rating": 4.7,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/corsair_h150i_elite_lcd.webp",
            "reviews": [
                {"review_text": "LCD display is a nice touch.", "rating": 5, "reviewer_name": "ShowBuilder", "review_date": "2024-09-15"}
            ]
        },
        {
            "name": "Fractal North Case",
            "description": "Minimalist ATX case with walnut front panel, mesh ventilation, and tool-free design.",
            "price": 149.0,
            "category": "Components",
            "brand": "Fractal Design",
            "rating": 4.8,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/fractal_north_case.webp",
            "reviews": [
                {"review_text": "Beautiful Scandinavian design.", "rating": 5, "reviewer_name": "AestheticBuilder", "review_date": "2024-10-01"}
            ]
        },

        # === FURNITURE (10) ===
        {
            "name": "Autonomous SmartDesk Pro",
            "description": "Electric standing desk with programmable height presets, 300lb capacity, and bamboo top option.",
            "price": 599.0,
            "category": "Furniture",
            "brand": "Autonomous",
            "rating": 4.5,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/autonomous_smartdesk_pro.webp",
            "reviews": [
                {"review_text": "Great desk for the price.", "rating": 4, "reviewer_name": "HomeOffice", "review_date": "2024-08-20"}
            ]
        },
        {
            "name": "Branch Standing Desk",
            "description": "Premium electric standing desk with 3-stage frame, 355lb capacity, and cable management.",
            "price": 799.0,
            "category": "Furniture",
            "brand": "Branch",
            "rating": 4.7,
            "shipping_speed": "10-day",
            "image_file_path": "/images/products/branch_standing_desk.webp",
            "reviews": [
                {"review_text": "Solid build and smooth motors.", "rating": 5, "reviewer_name": "OfficePro", "review_date": "2024-09-25"}
            ]
        },
        {
            "name": "Flexispot E7 Pro",
            "description": "Dual motor standing desk with 440lb capacity, anti-collision system, and memory presets.",
            "price": 649.0,
            "category": "Furniture",
            "brand": "Flexispot",
            "rating": 4.6,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/flexispot_e7_pro.webp",
            "reviews": [
                {"review_text": "Heavy duty and reliable.", "rating": 5, "reviewer_name": "DeskEnthusiast", "review_date": "2024-10-10"}
            ]
        },
        {
            "name": "Secretlab Titan Evo",
            "description": "Ergonomic gaming chair with 4-way lumbar support, magnetic memory foam pillows.",
            "price": 519.0,
            "category": "Furniture",
            "brand": "Secretlab",
            "rating": 4.7,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/secretlab_titan_evo.webp",
            "reviews": [
                {"review_text": "Most comfortable chair for long sessions.", "rating": 5, "reviewer_name": "ProGamer", "review_date": "2024-08-15"}
            ]
        },
        {
            "name": "Herman Miller Aeron",
            "description": "Iconic ergonomic office chair with PostureFit SL, 8Z Pellicle mesh, and 12-year warranty.",
            "price": 1395.0,
            "category": "Furniture",
            "brand": "Herman Miller",
            "rating": 4.9,
            "shipping_speed": "10-day",
            "image_file_path": "/images/products/herman_miller_aeron.webp",
            "reviews": [
                {"review_text": "Worth every penny for your back.", "rating": 5, "reviewer_name": "ErgonomicFan", "review_date": "2024-07-20"}
            ]
        },
        {
            "name": "Herman Miller Embody",
            "description": "Advanced ergonomic chair with Pixelated support, breathable design, and dynamic matrix.",
            "price": 1795.0,
            "category": "Furniture",
            "brand": "Herman Miller",
            "rating": 4.9,
            "shipping_speed": "10-day",
            "image_file_path": "/images/products/herman_miller_embody.webp",
            "reviews": [
                {"review_text": "My back has never felt better.", "rating": 5, "reviewer_name": "WorkFromHome", "review_date": "2024-08-10"}
            ]
        },
        {
            "name": "Steelcase Gesture",
            "description": "Ergonomic chair designed for technology use with 360° arms and LiveBack support.",
            "price": 1299.0,
            "category": "Furniture",
            "brand": "Steelcase",
            "rating": 4.8,
            "shipping_speed": "10-day",
            "image_file_path": "/images/products/steelcase_gesture.webp",
            "reviews": [
                {"review_text": "Perfect for multi-device users.", "rating": 5, "reviewer_name": "TechWorker", "review_date": "2024-09-08"}
            ]
        },
        {
            "name": "Steelcase Leap",
            "description": "Ergonomic chair with Natural Glide system, LiveBack technology, and 4-way adjustable arms.",
            "price": 1199.0,
            "category": "Furniture",
            "brand": "Steelcase",
            "rating": 4.8,
            "shipping_speed": "10-day",
            "image_file_path": "/images/products/steelcase_leap.webp",
            "reviews": [
                {"review_text": "Best chair for long coding sessions.", "rating": 5, "reviewer_name": "Developer", "review_date": "2024-08-25"}
            ]
        },
        {
            "name": "Razer Iskur V2",
            "description": "Gaming chair with adaptive lumbar support, 4D armrests, and EPU synthetic leather.",
            "price": 649.0,
            "category": "Furniture",
            "brand": "Razer",
            "rating": 4.6,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/razer_iskur_v2.webp",
            "reviews": [
                {"review_text": "Razer quality in chair form.", "rating": 5, "reviewer_name": "RazerFan", "review_date": "2024-10-05"}
            ]
        },

        # === ACCESSORIES & DOCKS (12) ===
        {
            "name": "CalDigit TS4 Dock",
            "description": "Thunderbolt 4 dock with 18 ports, 98W charging, and support for dual 4K displays.",
            "price": 399.0,
            "category": "Accessories",
            "brand": "CalDigit",
            "rating": 4.7,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/caldigit_ts4_dock.webp",
            "reviews": [
                {"review_text": "Best dock on the market.", "rating": 5, "reviewer_name": "DockMaster", "review_date": "2024-09-28"}
            ]
        },
        {
            "name": "CalDigit Element Hub",
            "description": "Compact Thunderbolt 4 hub with 4 ports and 60W charging in aluminum design.",
            "price": 179.0,
            "category": "Accessories",
            "brand": "CalDigit",
            "rating": 4.6,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/caldigit_element_hub.webp",
            "reviews": [
                {"review_text": "Simple but effective TB4 hub.", "rating": 5, "reviewer_name": "MinimalistSetup", "review_date": "2024-10-12"}
            ]
        },
        {
            "name": "Voltaic USB4 Dock",
            "description": "USB4 docking station with 15 ports, 100W PD, dual 4K@60Hz, and 2.5GbE.",
            "price": 299.0,
            "category": "Accessories",
            "brand": "Voltaic",
            "rating": 4.5,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/voltaic_usb4_dock.webp",
            "reviews": [
                {"review_text": "Great USB4 alternative to TB4.", "rating": 4, "reviewer_name": "PortHunter", "review_date": "2024-09-18"}
            ]
        },
        {
            "name": "Anker USB-C Hub 7-in-1",
            "description": "Portable USB-C hub with 4K HDMI, USB-A, SD card reader, and 100W power delivery.",
            "price": 49.0,
            "category": "Accessories",
            "brand": "Anker",
            "rating": 4.5,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/anker_usb_c_hub_7in1.webp",
            "reviews": [
                {"review_text": "Perfect travel companion.", "rating": 5, "reviewer_name": "RoadWarrior", "review_date": "2024-10-08"}
            ]
        },
        {
            "name": "HyperDrive 10-in-1",
            "description": "USB-C hub with dual 4K HDMI, USB-A, SD/microSD, and 100W pass-through charging.",
            "price": 99.0,
            "category": "Accessories",
            "brand": "Hyper",
            "rating": 4.6,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/hyper_hyperdrive_10in1.webp",
            "reviews": [
                {"review_text": "Dual HDMI is essential for presentations.", "rating": 5, "reviewer_name": "BusinessTraveler", "review_date": "2024-09-22"}
            ]
        },
        {
            "name": "Razer Gigantus V2 XXL",
            "description": "Extra-large gaming mouse pad with micro-textured cloth surface and anti-slip rubber base.",
            "price": 29.0,
            "category": "Accessories",
            "brand": "Razer",
            "rating": 4.6,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/razer_gigantus_v2_xxl.webp",
            "reviews": [
                {"review_text": "Covers my entire desk perfectly.", "rating": 5, "reviewer_name": "GamerPro", "review_date": "2024-10-05"}
            ]
        },
        {
            "name": "SteelSeries QcK Heavy",
            "description": "Premium cloth gaming mouse pad with extra-thick rubber base and optimized surface.",
            "price": 34.0,
            "category": "Accessories",
            "brand": "SteelSeries",
            "rating": 4.7,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/steelseries_qck_heavy.webp",
            "reviews": [
                {"review_text": "The thickness provides cushion for wrist.", "rating": 5, "reviewer_name": "ProPlayer", "review_date": "2024-09-15"}
            ]
        },
        {
            "name": "Logitech Desk Mat Studio",
            "description": "Premium desk mat with spill-resistant coating, anti-slip base, and subtle branding.",
            "price": 39.0,
            "category": "Accessories",
            "brand": "Logitech",
            "rating": 4.5,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/logitech_desk_mat_studio.webp",
            "reviews": [
                {"review_text": "Clean look for productivity setup.", "rating": 5, "reviewer_name": "DeskSetup", "review_date": "2024-10-20"}
            ]
        },
        {
            "name": "Ergotron LX Monitor Arm",
            "description": "Premium monitor arm with smooth motion, cable management, and support for monitors up to 34 inches.",
            "price": 179.0,
            "category": "Accessories",
            "brand": "Ergotron",
            "rating": 4.8,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/ergotron_lx_monitor_arm.webp",
            "reviews": [
                {"review_text": "Rock solid arm, no wobble.", "rating": 5, "reviewer_name": "CleanDeskSetup", "review_date": "2024-09-05"}
            ]
        },
        {
            "name": "Ergotron LX Dual Monitor Arm",
            "description": "Premium dual monitor arm with side-by-side mounting and 25lb capacity per monitor.",
            "price": 349.0,
            "category": "Accessories",
            "brand": "Ergotron",
            "rating": 4.8,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/ergotron_lx_dual.webp",
            "reviews": [
                {"review_text": "Perfect for dual monitor setups.", "rating": 5, "reviewer_name": "DualScreenUser", "review_date": "2024-10-02"}
            ]
        },
        {
            "name": "Ergotron HX Heavy Duty Arm",
            "description": "Heavy duty monitor arm for ultrawide monitors up to 49 inches and 42 lbs.",
            "price": 399.0,
            "category": "Accessories",
            "brand": "Ergotron",
            "rating": 4.9,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/ergotron_hx_heavy_duty.webp",
            "reviews": [
                {"review_text": "Handles my 49-inch ultrawide perfectly.", "rating": 5, "reviewer_name": "UltrawideUser", "review_date": "2024-09-28"}
            ]
        },
        {
            "name": "Humanscale M8",
            "description": "Premium monitor arm with dynamic motion, integrated cable management, and modern design.",
            "price": 495.0,
            "category": "Accessories",
            "brand": "Humanscale",
            "rating": 4.7,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/humanscale_m8.webp",
            "reviews": [
                {"review_text": "Most elegant monitor arm available.", "rating": 5, "reviewer_name": "DesignFocused", "review_date": "2024-08-30"}
            ]
        },

        # === LIGHTING (6) ===
        {
            "name": "BenQ ScreenBar Plus",
            "description": "LED monitor light bar with asymmetric optical design, auto-dimming, and desk controller.",
            "price": 129.0,
            "category": "Lighting",
            "brand": "BenQ",
            "rating": 4.7,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/benq_screenbar_plus.webp",
            "reviews": [
                {"review_text": "Reduces eye strain significantly.", "rating": 5, "reviewer_name": "NightOwl", "review_date": "2024-10-12"}
            ]
        },
        {
            "name": "Elgato Key Light",
            "description": "Professional LED panel with 2800 lumens, edge-lit design, and app control.",
            "price": 199.0,
            "category": "Lighting",
            "brand": "Elgato",
            "rating": 4.8,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/elgato_key_light.webp",
            "reviews": [
                {"review_text": "Studio lighting for streamers.", "rating": 5, "reviewer_name": "ContentCreator", "review_date": "2024-10-08"}
            ]
        },
        {
            "name": "Logitech Litra Glow",
            "description": "Premium streaming light with TrueSoft technology, USB-C powered, and software control.",
            "price": 59.0,
            "category": "Lighting",
            "brand": "Logitech",
            "rating": 4.5,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/logitech_litra_glow.webp",
            "reviews": [
                {"review_text": "Perfect for video calls.", "rating": 5, "reviewer_name": "RemoteWorker", "review_date": "2024-09-20"}
            ]
        },
        {
            "name": "Luminos Ambient Bar",
            "description": "RGB ambient light bar with music sync, app control, and bias lighting modes.",
            "price": 79.0,
            "category": "Lighting",
            "brand": "Luminos",
            "rating": 4.4,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/luminos_ambient_bar.webp",
            "reviews": [
                {"review_text": "Great ambiance for gaming.", "rating": 4, "reviewer_name": "RGBFan", "review_date": "2024-10-15"}
            ]
        },
        {
            "name": "Helios Arc 360",
            "description": "Ring light with 18-inch diameter, bi-color LEDs, and smartphone holder.",
            "price": 129.0,
            "category": "Lighting",
            "brand": "Helios",
            "rating": 4.6,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/helios_arc_360.webp",
            "reviews": [
                {"review_text": "Perfect lighting for content creation.", "rating": 5, "reviewer_name": "Influencer", "review_date": "2024-09-10"}
            ]
        },

        # === WEBCAMS (4) ===
        {
            "name": "Logitech Brio 4K Webcam",
            "description": "4K HDR webcam with RightLight 3 auto light correction and noise-canceling mics.",
            "price": 199.0,
            "category": "Webcams",
            "brand": "Logitech",
            "rating": 4.5,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/logitech_brio_4k_webcam.webp",
            "reviews": [
                {"review_text": "Crystal clear video quality.", "rating": 5, "reviewer_name": "StreamPro", "review_date": "2024-09-25"}
            ]
        },
        {
            "name": "Razer Kiyo Pro Ultra",
            "description": "4K webcam with large sensor, HDR, and AI-powered background removal.",
            "price": 299.0,
            "category": "Webcams",
            "brand": "Razer",
            "rating": 4.7,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/razer_kiyo_pro_ultra.webp",
            "reviews": [
                {"review_text": "Best webcam for low light.", "rating": 5, "reviewer_name": "NightStreamer", "review_date": "2024-10-18"}
            ]
        },

        # === STREAMING (6) ===
        {
            "name": "Elgato Stream Deck XL",
            "description": "32 customizable LCD keys for live content creation, productivity, and streaming.",
            "price": 249.0,
            "category": "Streaming",
            "brand": "Elgato",
            "rating": 4.8,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/elgato_stream_deck_xl.webp",
            "reviews": [
                {"review_text": "Essential for any streamer.", "rating": 5, "reviewer_name": "TwitchStreamer", "review_date": "2024-09-30"}
            ]
        },
        {
            "name": "Elgato Stream Deck Plus",
            "description": "Stream Deck with 8 LCD keys, 4 rotary dials, and touch strip for creative control.",
            "price": 199.0,
            "category": "Streaming",
            "brand": "Elgato",
            "rating": 4.7,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/elgato_stream_deck_plus.webp",
            "reviews": [
                {"review_text": "Dials are great for audio mixing.", "rating": 5, "reviewer_name": "AudioMixer", "review_date": "2024-10-10"}
            ]
        },
        {
            "name": "Elgato Stream Deck Neo",
            "description": "Compact Stream Deck with 8 LCD keys and USB-C in a portable form factor.",
            "price": 99.0,
            "category": "Streaming",
            "brand": "Elgato",
            "rating": 4.6,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/elgato_stream_deck_neo.webp",
            "reviews": [
                {"review_text": "Perfect entry-level Stream Deck.", "rating": 5, "reviewer_name": "NewStreamer", "review_date": "2024-09-15"}
            ]
        },
        {
            "name": "Loupedeck CT",
            "description": "Creative console with rotary dials, touch buttons, and deep software integration.",
            "price": 549.0,
            "category": "Streaming",
            "brand": "Loupedeck",
            "rating": 4.5,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/loupedeck_ct.webp",
            "reviews": [
                {"review_text": "Best for photo and video editing.", "rating": 5, "reviewer_name": "PhotoEditor", "review_date": "2024-08-20"}
            ]
        },

        # === CREATIVE (6) ===
        {
            "name": "Wacom Cintiq 22",
            "description": "22-inch pen display with Pro Pen 2, 8192 pressure levels, and anti-glare film.",
            "price": 1199.0,
            "category": "Creative",
            "brand": "Wacom",
            "rating": 4.7,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/wacom_cintiq_22.webp",
            "reviews": [
                {"review_text": "Professional drawing experience.", "rating": 5, "reviewer_name": "DigitalArtist", "review_date": "2024-09-18"}
            ]
        },
        {
            "name": "Wacom Cintiq Pro 27",
            "description": "27-inch 4K pen display with Pro Pen 3, 120Hz refresh, and Wacom Link Plus.",
            "price": 3499.0,
            "category": "Creative",
            "brand": "Wacom",
            "rating": 4.9,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/wacom_cintiq_pro_27.webp",
            "reviews": [
                {"review_text": "The ultimate digital canvas.", "rating": 5, "reviewer_name": "ProIllustrator", "review_date": "2024-10-05"}
            ]
        },
        {
            "name": "Wacom Intuos Pro Large",
            "description": "Professional pen tablet with Pro Pen 2, multi-touch, and customizable ExpressKeys.",
            "price": 499.0,
            "category": "Creative",
            "brand": "Wacom",
            "rating": 4.8,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/wacom_intuos_pro_large.webp",
            "reviews": [
                {"review_text": "Industry standard for digital art.", "rating": 5, "reviewer_name": "ConceptArtist", "review_date": "2024-09-25"}
            ]
        },
        {
            "name": "Huion Kamvas Pro 24 4K",
            "description": "24-inch 4K pen display with PW517 pen, 140% sRGB, and adjustable stand.",
            "price": 899.0,
            "category": "Creative",
            "brand": "Huion",
            "rating": 4.6,
            "shipping_speed": "5-day",
            "image_file_path": "/images/products/huion_kamvas_pro_24_4k.webp",
            "reviews": [
                {"review_text": "Great Wacom alternative.", "rating": 5, "reviewer_name": "HobbyArtist", "review_date": "2024-10-12"}
            ]
        },

        # === VR/AR (3) ===
        {
            "name": "Apple Vision Pro",
            "description": "Spatial computer with M2 and R1 chips, micro-OLED displays, and visionOS.",
            "price": 3499.0,
            "category": "VR",
            "brand": "Apple",
            "rating": 4.6,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/apple_vision_pro.webp",
            "reviews": [
                {"review_text": "The future of computing.", "rating": 5, "reviewer_name": "TechEarlyAdopter", "review_date": "2024-10-20"}
            ]
        },
        {
            "name": "Apple Vision Pro 2",
            "description": "Next-gen spatial computer with M4 chip, improved displays, and enhanced passthrough.",
            "price": 2999.0,
            "category": "VR",
            "brand": "Apple",
            "rating": 4.8,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/apple_vision_pro_2.webp",
            "reviews": [
                {"review_text": "Big improvements over gen 1.", "rating": 5, "reviewer_name": "VREnthusiast", "review_date": "2024-11-08"}
            ]
        },

        # === NETWORKING (2) ===
        {
            "name": "Ubiquiti Dream Router",
            "description": "All-in-one router with WiFi 6, UniFi OS, and integrated security gateway.",
            "price": 199.0,
            "category": "Networking",
            "brand": "Ubiquiti",
            "rating": 4.6,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/ubiquiti_dream_router.webp",
            "reviews": [
                {"review_text": "UniFi ecosystem entry point.", "rating": 5, "reviewer_name": "NetworkAdmin", "review_date": "2024-09-08"}
            ]
        },

        # === CABLES & POWER (5) ===
        {
            "name": "Apple Thunderbolt 4 Pro Cable",
            "description": "3m Thunderbolt 4 cable with 40Gbps speeds, 100W charging, and braided design.",
            "price": 159.0,
            "category": "Cables",
            "brand": "Apple",
            "rating": 4.7,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/apple_thunderbolt_4_pro_cable.webp",
            "reviews": [
                {"review_text": "Finally a long TB4 cable.", "rating": 5, "reviewer_name": "CableFinder", "review_date": "2024-10-15"}
            ]
        },
        {
            "name": "Cable Matters Thunderbolt 4 Cable",
            "description": "2m Thunderbolt 4 certified cable with 40Gbps, 100W PD, and 8K video support.",
            "price": 49.0,
            "category": "Cables",
            "brand": "Cable Matters",
            "rating": 4.6,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/cable_matters_thunderbolt_4_cable.webp",
            "reviews": [
                {"review_text": "Great value TB4 cable.", "rating": 5, "reviewer_name": "CableHunter", "review_date": "2024-09-30"}
            ]
        },
        {
            "name": "Voltaic Power Hub",
            "description": "Desktop charging station with 4 USB-C PD ports, 200W total power, and LED display.",
            "price": 149.0,
            "category": "Power",
            "brand": "Voltaic",
            "rating": 4.5,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/voltaic_power_hub.webp",
            "reviews": [
                {"review_text": "Powers all my devices.", "rating": 5, "reviewer_name": "GadgetLover", "review_date": "2024-10-02"}
            ]
        },
        {
            "name": "BlueLounge CableBox",
            "description": "Cable management box with surge protection and ventilation for power strips.",
            "price": 39.0,
            "category": "Accessories",
            "brand": "BlueLounge",
            "rating": 4.4,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/blue_lounge_cable_box.webp",
            "reviews": [
                {"review_text": "Hides all my cables neatly.", "rating": 4, "reviewer_name": "CleanDesk", "review_date": "2024-09-18"}
            ]
        },
        {
            "name": "Tessera Cable Management Kit",
            "description": "Complete cable management solution with channels, clips, and velcro straps.",
            "price": 29.0,
            "category": "Accessories",
            "brand": "Tessera",
            "rating": 4.5,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/tessera_cable_management_kit.webp",
            "reviews": [
                {"review_text": "Finally organized my desk cables.", "rating": 5, "reviewer_name": "CableManager", "review_date": "2024-10-08"}
            ]
        },

        # === ADDITIONAL PRODUCTS TO REACH 100 ===
        {
            "name": "Keychron K8 Pro",
            "description": "Tenkeyless wireless mechanical keyboard with QMK/VIA support, hot-swap, and RGB backlight.",
            "price": 149.0,
            "category": "Keyboards",
            "brand": "Keychron",
            "rating": 4.6,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/keychron_q1_pro.webp",
            "reviews": [
                {"review_text": "Great TKL option from Keychron.", "rating": 5, "reviewer_name": "TKLFan", "review_date": "2024-10-25"}
            ]
        },
        {
            "name": "Sony WF-1000XM5",
            "description": "Premium wireless earbuds with industry-leading ANC, LDAC Hi-Res audio, and 8hr battery.",
            "price": 299.0,
            "category": "Audio",
            "brand": "Sony",
            "rating": 4.8,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/sony_wh-1000xm5.webp",
            "reviews": [
                {"review_text": "Best earbuds money can buy.", "rating": 5, "reviewer_name": "EarbudUser", "review_date": "2024-11-01"}
            ]
        },
        {
            "name": "Samsung Odyssey G9",
            "description": "49-inch curved gaming monitor with 240Hz, 1ms response, and Quantum Mini-LED.",
            "price": 1299.0,
            "category": "Monitors",
            "brand": "Samsung",
            "rating": 4.7,
            "shipping_speed": "7-day",
            "image_file_path": "/images/products/lg_ultrafine_27_4k_monitor.webp",
            "reviews": [
                {"review_text": "Immersive ultrawide gaming.", "rating": 5, "reviewer_name": "UltrawideGamer", "review_date": "2024-10-18"}
            ]
        },
        {
            "name": "ASUS ROG Ally X",
            "description": "Handheld gaming PC with AMD Z1 Extreme, 7-inch 120Hz display, and 80Wh battery.",
            "price": 799.0,
            "category": "Laptops",
            "brand": "ASUS",
            "rating": 4.5,
            "shipping_speed": "3-day",
            "image_file_path": "/images/products/razer_blade_18_2025.webp",
            "reviews": [
                {"review_text": "Steam Deck competitor done right.", "rating": 5, "reviewer_name": "HandheldGamer", "review_date": "2024-10-30"}
            ]
        },
        {
            "name": "Crucial P5 Plus 2TB",
            "description": "PCIe 4.0 NVMe SSD with up to 6,600MB/s read speeds and advanced error correction.",
            "price": 129.0,
            "category": "Storage",
            "brand": "Crucial",
            "rating": 4.6,
            "shipping_speed": "2-day",
            "image_file_path": "/images/products/samsung_990_pro_2tb.webp",
            "reviews": [
                {"review_text": "Solid value for PCIe 4.0.", "rating": 5, "reviewer_name": "StorageBudget", "review_date": "2024-09-22"}
            ]
        },
    ]

    async with async_session() as session:
        # Clear existing products and reviews for fresh seed
        await session.execute(delete(Review))
        await session.execute(delete(Product))
        await session.commit()

        for product_data in products_data:
            reviews_data = product_data.pop("reviews", [])

            product = Product(**product_data)
            session.add(product)
            await session.flush()  # Get the product ID

            # Add reviews
            for review_data in reviews_data:
                review = Review(product_id=product.id, **review_data)
                session.add(review)

        await session.commit()
        print(f"Seeded {len(products_data)} products")


if __name__ == "__main__":
    asyncio.run(seed_products())
