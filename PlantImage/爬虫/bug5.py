import os
import re
import time
import json
import mysql.connector
from bs4 import BeautifulSoup
import requests
from urllib.parse import quote
from tqdm import tqdm
import random
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
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0'
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
    """创建植物信息表（如果不存在）"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS plants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            latin_name VARCHAR(255) NOT NULL,
            chinese_name VARCHAR(255),
            common_name VARCHAR(255),
            family VARCHAR(255),
            genus VARCHAR(255),
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
        logging.info("数据表已准备就绪")
    except mysql.connector.Error as e:
        logging.error(f"创建表错误: {e}")


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


def get_attribute_safe(driver, selector, attribute, wait_time=5):
    """安全地获取元素属性，如果元素不存在返回空字符串"""
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element.get_attribute(attribute) or ""
    except (TimeoutException, NoSuchElementException):
        return ""
    except Exception as e:
        logging.debug(f"获取元素 {selector} 的属性 {attribute} 时出错: {e}")
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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".infotitlediv"))
        )

        # 提取中文名
        chinese_name = get_text_safe(driver, ".infocname")

        # 提取俗名/通用名
        common_name = ""
        infomore_text = get_text_safe(driver, ".infomore")
        if infomore_text:
            match = re.search(r'俗名：(.+)', infomore_text)
            if match:
                common_name = match.group(1).strip()

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
                elif "属" in text:
                    genus = text
        except Exception as e:
            logging.debug(f"提取科属信息时出错: {e}")

        # 提取形态特征
        description = ""
        try:
            # 点击形态特征标签（如果需要）
            morph_tab = driver.find_element(By.CSS_SELECTOR, "#list_mp11")
            if not "display: block" in morph_tab.get_attribute("style"):
                morph_tab.click()
                time.sleep(1)  # 等待内容加载

            # 获取形态特征表格中的所有行
            rows = driver.find_elements(By.CSS_SELECTOR, "#cont_mp11 table.t2 tr")
            for row in rows:
                try:
                    feature = row.find_element(By.CSS_SELECTOR, ".td1").text.strip()
                    value = row.find_element(By.CSS_SELECTOR, ".td2").text.strip()
                    description += f"{feature} {value}\n"
                except NoSuchElementException:
                    continue
        except Exception as e:
            logging.debug(f"提取形态特征时出错: {e}")

        # 提取生态习性
        ecology = ""
        try:
            # 点击生态习性标签（如果需要）
            eco_tab = driver.find_element(By.CSS_SELECTOR, "#list_mp12")
            if not "display: block" in eco_tab.get_attribute("style"):
                eco_tab.click()
                time.sleep(1)  # 等待内容加载

            # 获取生态习性表格中的所有行
            rows = driver.find_elements(By.CSS_SELECTOR, "#cont_mp12 table.t2 tr")
            for row in rows:
                try:
                    feature = row.find_element(By.CSS_SELECTOR, ".td1").text.strip()
                    value = row.find_element(By.CSS_SELECTOR, ".td2").text.strip()
                    ecology += f"{feature} {value}\n"
                except NoSuchElementException:
                    continue
        except Exception as e:
            logging.debug(f"提取生态习性时出错: {e}")

        # 提取功用价值
        plant_usage = ""
        try:
            # 点击功用价值标签（如果需要）
            usage_tab = driver.find_element(By.CSS_SELECTOR, "#list_mp20")
            if not "display: none" in usage_tab.get_attribute("style"):
                usage_tab.click()
                time.sleep(1)  # 等待内容加载

                # 获取功用价值表格中的所有行
                rows = driver.find_elements(By.CSS_SELECTOR, "#cont_mp20 table.t2 tr")
                for row in rows:
                    try:
                        feature = row.find_element(By.CSS_SELECTOR, ".td1").text.strip()
                        value = row.find_element(By.CSS_SELECTOR, ".td2").text.strip()
                        plant_usage += f"{feature} {value}\n"
                    except NoSuchElementException:
                        continue
        except (NoSuchElementException, Exception) as e:
            logging.debug(f"提取功用价值时出错: {e}")

        # 提取图片URL
        image_url = ""
        try:
            img_element = driver.find_element(By.CSS_SELECTOR, "#imglist img")
            image_url = img_element.get_attribute("src") or ""
            if image_url.startswith("//"):
                image_url = f"https:{image_url}"
        except NoSuchElementException:
            pass
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

        # 输出详细日志信息
        logging.debug(f"成功提取 {latin_name} 的数据")
        logging.debug(f"中文名: {chinese_name}")
        logging.debug(f"科属: {family} / {genus}")
        logging.debug(f"数据完整性: {'完整' if complete_flag else '不完整'}")

        return plant_data, None

    except TimeoutException:
        return None, "页面加载超时"
    except Exception as e:
        logging.exception(f"抓取 {latin_name} 时发生错误")
        return None, f"抓取错误: {str(e)}"


def save_to_database(conn, plant_data):
    """保存或更新植物数据到数据库"""
    try:
        if not conn:
            logging.error("数据库连接不可用")
            return False

        cursor = conn.cursor()

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

        # 植物列表 - 这里应该替换为您自己的植物拉丁名列表
        plant_list = ["Abies alba", "Abeliophyllum distichum", "Achyranthes aspera"]  # 示例植物

        # 使用tqdm显示进度
        for plant in tqdm(plant_list, desc="爬取植物数据"):
            print(f"\n正在处理: {plant}")

            # 随机延迟，防止请求过快
            time.sleep(random.uniform(2, 5))

            # 抓取植物数据
            plant_data, error = scrape_plant_data(driver, plant)

            if error:
                logging.error(f"植物 {plant} 抓取失败: {error}")
                continue

            if not plant_data:
                logging.warning(f"未找到植物 {plant} 的数据")
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

            print("-" * 50)

    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        logging.exception("程序执行过程中出现未知错误")
    finally:
        # 关闭浏览器
        if driver:
            driver.quit()
            logging.info("浏览器驱动已关闭")

        # 关闭数据库连接
        if conn:
            conn.close()
            logging.info("数据库连接已关闭")


if __name__ == "__main__":
    main()