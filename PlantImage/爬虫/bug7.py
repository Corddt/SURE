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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.common.alert import Alert
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("recovery_scraper.log"),
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

# 保存爬取进度的文件
PROGRESS_FILE = 'scraping_progress.json'
RECOVERY_PROGRESS_FILE = 'recovery_progress.json'


def get_failed_plants():
    """获取失败的植物列表"""
    # 方法1：从progress文件中获取failed列表
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                return progress.get("failed", [])
        except Exception as e:
            logging.error(f"读取progress文件失败: {e}")

    # 方法2：从数据库中计算缺失的植物
    missing_plants = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 获取数据库中已有的植物
        cursor.execute("SELECT latin_name FROM plants")
        existing_plants = {row[0] for row in cursor.fetchall()}

        # 获取所有植物列表
        plant_directory = "D:/PlantData/PlantImage"
        all_plants = [folder.replace('/', '') for folder in os.listdir(plant_directory)
                      if os.path.isdir(os.path.join(plant_directory, folder))]

        # 计算缺失的植物
        missing_plants = [plant for plant in all_plants if plant not in existing_plants]

        conn.close()
    except Exception as e:
        logging.error(f"从数据库计算缺失植物失败: {e}")

    return missing_plants


def load_recovery_progress():
    """加载恢复进度"""
    if os.path.exists(RECOVERY_PROGRESS_FILE):
        try:
            with open(RECOVERY_PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"completed": [], "failed": []}
    return {"completed": [], "failed": []}


def save_recovery_progress(progress):
    """保存恢复进度"""
    with open(RECOVERY_PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def setup_driver(use_proxy=False, proxy=None):
    """设置并返回Chrome浏览器驱动"""
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
            # ... 其他用户代理 ...
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

        # 添加代理（如果需要）
        if use_proxy and proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')

        # 自动安装ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # 设置页面加载超时时间
        driver.set_page_load_timeout(30)

        return driver
    except Exception as e:
        logging.error(f"设置Chrome驱动时出错: {e}")
        raise


def handle_alert(driver):
    """处理弹出的警告框"""
    try:
        alert = Alert(driver)
        alert_text = alert.text
        logging.warning(f"检测到警告框: {alert_text}")
        alert.accept()
        return True
    except:
        return False


def scrape_plant_data(driver, latin_name):
    """使用Selenium抓取植物数据，增加了弹窗处理"""
    search_url = f"https://www.iplant.cn/info/{latin_name}"

    try:
        # 访问URL
        driver.get(search_url)

        # 处理可能出现的警告框
        if handle_alert(driver):
            logging.warning("已处理警告，等待一段时间后重试")
            return None, "需要等待访问限制重置"

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
        chinese_name = ""
        try:
            chinese_name_elems = driver.find_elements(By.CSS_SELECTOR, ".infocname")
            if chinese_name_elems:
                chinese_name = chinese_name_elems[0].text.strip()
        except:
            pass

        # 提取俗名/通用名
        common_name = ""
        try:
            infomore_div = driver.find_elements(By.CSS_SELECTOR, ".infomore")
            if infomore_div:
                common_name_text = infomore_div[0].text.strip()
                if "俗名：" in common_name_text:
                    common_name = common_name_text.split("俗名：")[1].strip()
        except:
            pass

        # 提取科属信息
        family = ""
        genus = ""
        try:
            class_elements = driver.find_elements(By.CSS_SELECTOR, "#rightclasssys div a")
            for element in class_elements:
                text = element.text.strip()
                if "科" in text and not family:
                    family = text
                elif "属" in text and not genus:
                    genus = text
        except:
            pass

        # 提取形态特征
        description = ""
        try:
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
        except:
            pass

        # 提取生态习性
        ecology = ""
        try:
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
        except:
            pass

        # 提取功用价值
        plant_usage = ""
        try:
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
        except:
            pass

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
        except:
            pass

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

    except UnexpectedAlertPresentException as e:
        # 处理弹出的警告框
        handle_alert(driver)
        logging.warning(f"处理警告框: {e.alert_text if hasattr(e, 'alert_text') else 'Unknown alert'}")
        return None, f"访问受限: {e.alert_text if hasattr(e, 'alert_text') else 'Unknown alert'}"
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


def main():
    # 获取失败的植物列表
    failed_plants = get_failed_plants()

    if not failed_plants:
        logging.error("未找到失败的植物列表，程序终止")
        return

    # 加载恢复进度
    recovery_progress = load_recovery_progress()
    completed_plants = set(recovery_progress.get("completed", []))
    failed_again_plants = set(recovery_progress.get("failed", []))

    # 过滤已完成或再次失败的植物
    remaining_plants = [p for p in failed_plants if p not in completed_plants and p not in failed_again_plants]

    # 检查是否有剩余植物需要爬取
    if not remaining_plants:
        logging.info("所有失败的植物已处理完毕")
        return

    logging.info(f"找到 {len(remaining_plants)} 个待恢复处理植物")

    # 创建Chrome浏览器驱动
    driver = None
    conn = None

    try:
        # 设置浏览器
        driver = setup_driver()

        # 创建数据库连接
        conn = mysql.connector.connect(**DB_CONFIG)
        if not conn:
            logging.error("无法建立数据库连接，程序终止")
            return

        # 使用tqdm显示进度
        for plant in tqdm(remaining_plants, desc="恢复爬取植物数据"):
            print(f"\n正在处理: {plant}")

            try:
                # 随机延迟，防止请求过快，考虑到访问限制，增加等待时间
                time.sleep(random.uniform(5, 10))

                # 抓取植物数据
                plant_data, error = scrape_plant_data(driver, plant)

                if error:
                    if "访问受限" in error or "需要等待" in error:
                        logging.warning(f"植物 {plant} 访问受限，将暂停爬取")
                        # 遇到访问限制，可以考虑暂停更长时间
                        waiting_time = random.randint(30, 60)  # 暂停30-60秒
                        print(f"检测到访问限制，等待 {waiting_time} 秒后继续...")
                        time.sleep(waiting_time)

                        # 重新尝试爬取
                        plant_data, error = scrape_plant_data(driver, plant)

                        # 如果仍然失败，可以考虑重启浏览器或使用代理
                        if error:
                            logging.error(f"植物 {plant} 重试后仍然失败: {error}")
                            failed_again_plants.add(plant)
                            recovery_progress["failed"] = list(failed_again_plants)
                            save_recovery_progress(recovery_progress)

                            # 重启浏览器
                            driver.quit()
                            driver = setup_driver()
                            continue
                    else:
                        logging.error(f"植物 {plant} 抓取失败: {error}")
                        failed_again_plants.add(plant)
                        recovery_progress["failed"] = list(failed_again_plants)
                        save_recovery_progress(recovery_progress)
                        continue

                if not plant_data:
                    logging.warning(f"未找到植物 {plant} 的数据")
                    failed_again_plants.add(plant)
                    recovery_progress["failed"] = list(failed_again_plants)
                    save_recovery_progress(recovery_progress)
                    continue

                # 保存到数据库
                success = save_to_database(conn, plant_data)

                # 输出状态信息
                print(f"植物: {plant}")
                print(f"中文名: {plant_data.get('chinese_name', '')}")
                print(f"科属: {plant_data.get('family', '')} / {plant_data.get('genus', '')}")

                if plant_data["complete_flag"] == 0:
                    print(f"数据完整性: 不完整")
                else:
                    print(f"数据完整性: 完整")

                # 更新进度
                if success:
                    completed_plants.add(plant)
                    recovery_progress["completed"] = list(completed_plants)
                    save_recovery_progress(recovery_progress)

                print("-" * 50)

            except Exception as e:
                logging.exception(f"处理植物 {plant} 时出现未知错误")
                failed_again_plants.add(plant)
                recovery_progress["failed"] = list(failed_again_plants)
                save_recovery_progress(recovery_progress)

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