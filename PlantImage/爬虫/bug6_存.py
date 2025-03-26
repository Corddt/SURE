import os
import time
import json
import random
import mysql.connector
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("plant_scraper.log"),
        logging.StreamHandler()
    ]
)

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "plants_db",
    "charset": "utf8mb4"
}

# 保存未完成数据的文件
INCOMPLETE_DATA_FILE = 'incomplete_plants.json'
# 保存爬取进度的文件
PROGRESS_FILE = 'scraping_progress.json'


def get_plant_list_from_directory(directory_path):
    """从目录结构中获取植物拉丁名列表"""
    plant_list = []

    try:
        # 获取目录中的所有文件夹
        for folder in os.listdir(directory_path):
            folder_path = os.path.join(directory_path, folder)
            # 确保是目录
            if os.path.isdir(folder_path):
                # 文件夹名格式应为 "Genus species"
                plant_list.append(folder.replace('/', ''))

        logging.info(f"从目录中找到 {len(plant_list)} 个植物名")
        return plant_list
    except Exception as e:
        logging.error(f"读取目录时出错: {e}")
        return []


def load_progress():
    """加载爬取进度"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"completed": [], "failed": []}
    return {"completed": [], "failed": []}


def save_progress(progress):
    """保存爬取进度"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def setup_driver():
    """设置并返回Chrome无头浏览器驱动"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # 添加随机UA
        user_agents = [
            # Windows + Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',

            # Windows + Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',

            # Windows + Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.62',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.38',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.47',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.44',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',

            # macOS + Chrome
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',

            # macOS + Firefox
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:92.0) Gecko/20100101 Firefox/92.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:93.0) Gecko/20100101 Firefox/93.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 12.0; rv:93.0) Gecko/20100101 Firefox/93.0',

            # macOS + Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',

            # Linux + Chrome
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',

            # Linux + Firefox
            'Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0',

            # 最新版浏览器 (2023-2024)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',

            # 移动设备 - Android
            'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.50 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.135 Mobile Safari/537.36',

            # 移动设备 - iOS
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

        # 自动安装ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # 设置页面加载超时时间
        driver.set_page_load_timeout(30)

        return driver
    except Exception as e:
        logging.error(f"设置Chrome驱动时出错: {e}")
        raise


def create_connection():
    """创建数据库连接"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        logging.error(f"数据库连接错误: {e}")
        return None


def create_table(conn):
    """创建植物信息表（如果不存在）并确保字段长度足够"""
    try:
        cursor = conn.cursor()

        # 首先检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'plants'")
        table_exists = cursor.fetchone()

        if table_exists:
            # 如果表已存在，修改字段长度
            alterations = [
                "ALTER TABLE plants MODIFY chinese_name VARCHAR(500)",
                "ALTER TABLE plants MODIFY common_name TEXT",  # 使用TEXT类型存储可能很长的内容
                "ALTER TABLE plants MODIFY family VARCHAR(500)",
                "ALTER TABLE plants MODIFY genus VARCHAR(500)"
            ]

            for alter_sql in alterations:
                try:
                    cursor.execute(alter_sql)
                    conn.commit()
                    logging.info(f"执行SQL: {alter_sql}")
                except mysql.connector.Error as err:
                    if err.errno == 1060:  # Duplicate column name
                        logging.debug(f"字段已存在: {err}")
                    else:
                        logging.warning(f"修改表结构时出错: {err}")
        else:
            # 创建新表，使用更大的字段长度
            cursor.execute("""
            CREATE TABLE plants (
                id INT AUTO_INCREMENT PRIMARY KEY,
                latin_name VARCHAR(255) NOT NULL,
                chinese_name VARCHAR(500),
                common_name TEXT,
                family VARCHAR(500),
                genus VARCHAR(500),
                description TEXT,
                ecology TEXT,
                plant_usage TEXT,
                image_url VARCHAR(2048),
                complete_flag TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

        conn.commit()
        logging.info("数据表已准备就绪，字段长度已调整")
    except mysql.connector.Error as e:
        logging.error(f"创建/修改表错误: {e}")


def get_text_safe(driver, selector, wait_time=5):
    """安全地获取元素文本，如果元素不存在返回空字符串"""
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element.text.strip()
    except (TimeoutException, NoSuchElementException):
        return ""
    except Exception as e:
        logging.debug(f"获取元素 {selector} 文本时出错: {e}")
        return ""


def scrape_plant_data(driver, latin_name):
    """使用Selenium抓取植物数据"""
    search_url = f"https://www.iplant.cn/info/{latin_name}"

    try:
        # 访问URL
        driver.get(search_url)

        # 检查是否找到植物
        if "找不到符合条件的数据" in driver.page_source:
            return None, "植物未找到"

        # 等待页面加载完成
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".infotitlediv"))
            )
        except TimeoutException:
            return None, "页面加载超时或植物不存在"

        # 提取中文名
        chinese_name = get_text_safe(driver, ".infocname")

        # 提取俗名/通用名
        common_name = ""
        infomore_div = driver.find_elements(By.CSS_SELECTOR, ".infomore")
        if infomore_div:
            common_name_text = infomore_div[0].text.strip()
            if "俗名：" in common_name_text:
                common_name = common_name_text.split("俗名：")[1].strip()

        # 提取科属信息
        family = ""
        genus = ""
        try:
            # 科信息通常在右侧分类树中
            class_elements = driver.find_elements(By.CSS_SELECTOR, "#rightclasssys div a")
            for element in class_elements:
                text = element.text.strip()
                if "科" in text and not family:
                    family = text
                elif "属" in text and not genus:
                    genus = text
        except Exception as e:
            logging.debug(f"提取科属信息时出错: {e}")

        # 提取形态特征
        description = ""
        try:
            # 查看形态特征是否可见
            morphology_divs = driver.find_elements(By.CSS_SELECTOR, "#cont_mp11")
            if morphology_divs:
                # 如果形态特征标签不可见，点击显示
                if "display: none" in morphology_divs[0].get_attribute("style"):
                    morph_tab = driver.find_element(By.CSS_SELECTOR, "#list_mp11")
                    driver.execute_script("arguments[0].click();", morph_tab)
                    time.sleep(1)  # 等待内容加载

                # 获取形态特征表格
                rows = driver.find_elements(By.CSS_SELECTOR, "#cont_mp11 table.t2 tr")
                for row in rows:
                    try:
                        feature_cells = row.find_elements(By.CSS_SELECTOR, ".td1")
                        value_cells = row.find_elements(By.CSS_SELECTOR, ".td2")

                        if feature_cells and value_cells:
                            feature = feature_cells[0].text.strip()
                            value = value_cells[0].text.strip()
                            description += f"{feature} {value}\n"
                    except:
                        continue
        except Exception as e:
            logging.debug(f"提取形态特征时出错: {e}")

        # 提取生态习性
        ecology = ""
        try:
            # 查看生态习性是否可见
            ecology_divs = driver.find_elements(By.CSS_SELECTOR, "#cont_mp12")
            if ecology_divs:
                # 如果生态习性标签不可见，点击显示
                if "display: none" in ecology_divs[0].get_attribute("style"):
                    eco_tab = driver.find_element(By.CSS_SELECTOR, "#list_mp12")
                    driver.execute_script("arguments[0].click();", eco_tab)
                    time.sleep(1)  # 等待内容加载

                # 获取生态习性表格
                rows = driver.find_elements(By.CSS_SELECTOR, "#cont_mp12 table.t2 tr")
                for row in rows:
                    try:
                        feature_cells = row.find_elements(By.CSS_SELECTOR, ".td1")
                        value_cells = row.find_elements(By.CSS_SELECTOR, ".td2")

                        if feature_cells and value_cells:
                            feature = feature_cells[0].text.strip()
                            value = value_cells[0].text.strip()
                            ecology += f"{feature} {value}\n"
                    except:
                        continue
        except Exception as e:
            logging.debug(f"提取生态习性时出错: {e}")

        # 提取功用价值
        plant_usage = ""
        try:
            # 查看功用价值是否存在
            usage_tabs = driver.find_elements(By.CSS_SELECTOR, "#list_mp20")
            if usage_tabs:
                # 如果功用价值标签存在，点击显示
                driver.execute_script("arguments[0].click();", usage_tabs[0])
                time.sleep(1)  # 等待内容加载

                # 获取功用价值表格
                usage_divs = driver.find_elements(By.CSS_SELECTOR, "#cont_mp20")
                if usage_divs:
                    rows = driver.find_elements(By.CSS_SELECTOR, "#cont_mp20 table.t2 tr")
                    for row in rows:
                        try:
                            feature_cells = row.find_elements(By.CSS_SELECTOR, ".td1")
                            value_cells = row.find_elements(By.CSS_SELECTOR, ".td2")

                            if feature_cells and value_cells:
                                feature = feature_cells[0].text.strip()
                                value = value_cells[0].text.strip()
                                plant_usage += f"{feature} {value}\n"
                        except:
                            continue
        except Exception as e:
            logging.debug(f"提取功用价值时出错: {e}")

        # 提取图片URL
        image_url = ""
        try:
            img_elements = driver.find_elements(By.CSS_SELECTOR, "#imglist img")
            if img_elements:
                src = img_elements[0].get_attribute("src")
                if src:
                    image_url = src
                    if image_url.startswith("//"):
                        image_url = f"https:{image_url}"
        except Exception as e:
            logging.debug(f"提取图片URL时出错: {e}")

        # 判断数据完整性
        complete_flag = 1 if (chinese_name and family and genus and description) else 0

        # 收集数据
        plant_data = {
            "latin_name": latin_name,
            "chinese_name": chinese_name,
            "common_name": common_name,
            "family": family,
            "genus": genus,
            "description": description.strip(),
            "ecology": ecology.strip(),
            "plant_usage": plant_usage.strip(),
            "image_url": image_url,
            "complete_flag": complete_flag
        }

        return plant_data, None

    except TimeoutException:
        return None, "页面加载超时"
    except Exception as e:
        logging.exception(f"抓取 {latin_name} 时发生错误")
        return None, f"抓取错误: {str(e)}"


def save_to_database(conn, plant_data):
    """保存或更新植物数据到数据库，添加数据截断处理"""
    try:
        if not conn:
            logging.error("数据库连接不可用")
            return False

        cursor = conn.cursor()

        # 数据预处理：截断过长的字段（必要时）
        # 由于我们已经修改为更大的字段长度或TEXT类型，这一步可能不必要
        # 但为保险起见，我们仍然对VARCHAR字段进行截断处理
        if plant_data["chinese_name"] and len(plant_data["chinese_name"]) > 500:
            plant_data["chinese_name"] = plant_data["chinese_name"][:497] + "..."
            logging.warning(f"截断了过长的chinese_name字段: {plant_data['latin_name']}")

        if plant_data["family"] and len(plant_data["family"]) > 500:
            plant_data["family"] = plant_data["family"][:497] + "..."
            logging.warning(f"截断了过长的family字段: {plant_data['latin_name']}")

        if plant_data["genus"] and len(plant_data["genus"]) > 500:
            plant_data["genus"] = plant_data["genus"][:497] + "..."
            logging.warning(f"截断了过长的genus字段: {plant_data['latin_name']}")

        # 检查植物是否已存在
        cursor.execute(
            "SELECT id, complete_flag FROM plants WHERE latin_name = %s",
            (plant_data["latin_name"],)
        )
        result = cursor.fetchone()

        if result:
            plant_id, existing_complete_flag = result

            # 只有当现有数据不完整或新数据更完整时才更新
            if existing_complete_flag == 0 or plant_data["complete_flag"] == 1:
                cursor.execute("""
                UPDATE plants SET 
                    chinese_name = %s,
                    common_name = %s, 
                    family = %s,
                    genus = %s,
                    description = %s,
                    ecology = %s,
                    plant_usage = %s,
                    image_url = %s,
                    complete_flag = %s
                WHERE id = %s
                """, (
                    plant_data["chinese_name"],
                    plant_data["common_name"],
                    plant_data["family"],
                    plant_data["genus"],
                    plant_data["description"],
                    plant_data["ecology"],
                    plant_data["plant_usage"],
                    plant_data["image_url"],
                    plant_data["complete_flag"],
                    plant_id
                ))
                conn.commit()
                logging.info(f"更新植物 {plant_data['latin_name']} 的数据")
                return True
            else:
                logging.info(f"跳过 {plant_data['latin_name']} - 现有数据已完整")
                return True
        else:
            # 插入新植物
            cursor.execute("""
            INSERT INTO plants (
                latin_name, chinese_name, common_name, family, genus, 
                description, ecology, plant_usage, image_url, complete_flag
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                plant_data["latin_name"],
                plant_data["chinese_name"],
                plant_data["common_name"],
                plant_data["family"],
                plant_data["genus"],
                plant_data["description"],
                plant_data["ecology"],
                plant_data["plant_usage"],
                plant_data["image_url"],
                plant_data["complete_flag"]
            ))
            conn.commit()
            logging.info(f"添加新植物 {plant_data['latin_name']} 到数据库")
            return True
    except mysql.connector.Error as e:
        logging.error(f"数据库操作错误: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logging.exception(f"保存数据时出现未知错误")
        if conn:
            conn.rollback()
        return False


def save_incomplete_data(plant_data):
    """将不完整的数据保存到JSON文件"""
    try:
        # 确保植物数据有拉丁名
        if not plant_data or "latin_name" not in plant_data:
            return

        # 加载现有的不完整数据文件
        incomplete_data = []
        if os.path.exists(INCOMPLETE_DATA_FILE):
            with open(INCOMPLETE_DATA_FILE, 'r', encoding='utf-8') as f:
                try:
                    incomplete_data = json.load(f)
                except json.JSONDecodeError:
                    incomplete_data = []

        # 添加新的不完整数据
        incomplete_data.append({
            "latin_name": plant_data["latin_name"],
            "chinese_name": plant_data["chinese_name"],
            "family": plant_data["family"],
            "genus": plant_data["genus"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # 保存更新后的不完整数据文件
        with open(INCOMPLETE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(incomplete_data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logging.error(f"保存不完整数据到JSON文件时出错: {e}")


def main():
    # 获取植物列表
    plant_directory = "D:/PlantData/PlantImage"  # 使用您的实际路径
    plant_list = get_plant_list_from_directory(plant_directory)

    if not plant_list:
        logging.error("未找到植物列表，程序终止")
        return

    # 加载进度
    progress = load_progress()
    completed_plants = set(progress["completed"])
    failed_plants = set(progress["failed"])

    # 过滤已完成或失败的植物
    remaining_plants = [p for p in plant_list if p not in completed_plants and p not in failed_plants]

    # 检查是否有剩余植物需要爬取
    if not remaining_plants:
        logging.info("所有植物已处理完毕")
        return

    logging.info(f"找到 {len(remaining_plants)} 个待处理植物")

    # 创建Chrome无头浏览器驱动
    driver = None
    conn = None

    try:
        # 设置浏览器
        driver = setup_driver()

        # 创建数据库连接
        conn = create_connection()
        if not conn:
            logging.error("无法建立数据库连接，程序终止")
            return

        # 创建数据表
        create_table(conn)

        # 使用tqdm显示进度
        for plant in tqdm(remaining_plants, desc="爬取植物数据"):
            print(f"\n正在处理: {plant}")

            try:
                # 随机延迟，防止请求过快
                time.sleep(random.uniform(2, 5))

                # 抓取植物数据
                plant_data, error = scrape_plant_data(driver, plant)

                if error:
                    logging.error(f"植物 {plant} 抓取失败: {error}")
                    failed_plants.add(plant)
                    progress["failed"] = list(failed_plants)
                    save_progress(progress)
                    continue

                if not plant_data:
                    logging.warning(f"未找到植物 {plant} 的数据")
                    failed_plants.add(plant)
                    progress["failed"] = list(failed_plants)
                    save_progress(progress)
                    continue

                # 保存到数据库
                success = save_to_database(conn, plant_data)

                # 输出状态信息
                print(f"植物: {plant}")
                print(f"中文名: {plant_data.get('chinese_name', '')}")
                print(f"科属: {plant_data.get('family', '')} / {plant_data.get('genus', '')}")

                if plant_data["complete_flag"] == 0:
                    print(f"数据完整性: 不完整")
                    # 保存不完整的数据以便后续处理
                    save_incomplete_data(plant_data)
                else:
                    print(f"数据完整性: 完整")

                # 更新进度
                if success:
                    completed_plants.add(plant)
                    progress["completed"] = list(completed_plants)
                    save_progress(progress)

                print("-" * 50)

            except Exception as e:
                logging.exception(f"处理植物 {plant} 时出现未知错误")
                failed_plants.add(plant)
                progress["failed"] = list(failed_plants)
                save_progress(progress)

                # 如果浏览器有问题，重新初始化
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = setup_driver()

    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        logging.exception("程序执行过程中出现未知错误")
    finally:
        # 关闭浏览器
        if driver:
            try:
                driver.quit()
                logging.info("浏览器驱动已关闭")
            except:
                pass

        # 关闭数据库连接
        if conn:
            conn.close()
            logging.info("数据库连接已关闭")


if __name__ == "__main__":
    main()