import os
import re
import time
import json
import mysql.connector
from bs4 import BeautifulSoup
import requests
from urllib.parse import quote
from tqdm import tqdm

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "plants_db",
    "charset": "utf8mb4"
}


# 创建数据库连接
def create_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("数据库连接成功")
        return conn
    except mysql.connector.Error as e:
        print(f"数据库连接错误: {e}")
        return None


# 创建数据表
def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plants (
        id INT AUTO_INCREMENT PRIMARY KEY,
        latin_name VARCHAR(100) NOT NULL COMMENT '拉丁学名',
        chinese_name VARCHAR(50) COMMENT '中文学名',
        common_name VARCHAR(200) COMMENT '俗名',
        family VARCHAR(50) COMMENT '科',
        genus VARCHAR(50) COMMENT '属',
        description TEXT COMMENT '形态特征',
        ecology TEXT COMMENT '生态习性',
        plant_usage TEXT COMMENT '用途价值',
        image_url VARCHAR(255) COMMENT '图片URL',
        data_source VARCHAR(50) DEFAULT 'iPlant' COMMENT '数据来源',
        complete_flag TINYINT DEFAULT 0 COMMENT '数据完整度标志: 0=不完整, 1=完整',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        INDEX idx_latin_name (latin_name),
        INDEX idx_chinese_name (chinese_name),
        INDEX idx_complete (complete_flag)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """)
    conn.commit()
    print("数据表已创建或已存在")


# 从表格中提取信息
def extract_table_data(table):
    result = {}
    if not table:
        return result

    rows = table.find_all('tr')
    for row in rows:
        cells = row.find_all(['td'])
        if len(cells) >= 2:
            key_cell = cells[0]
            value_cell = cells[1]

            # 提取键（去除标签）
            key = key_cell.get_text(strip=True).replace('：', '').strip()
            # 移除span标签
            key = re.sub(r'<span.*?>|</span>', '', key if isinstance(key, str) else '')

            # 提取值
            value = value_cell.get_text(strip=True)
            # 清理值中的HTML标签
            value = re.sub(r'<.*?>', '', value if isinstance(value, str) else '')

            result[key] = value

    return result


# 从iPlant网站抓取植物信息
def scrape_plant_data(latin_name):
    """抓取植物数据并返回所需信息"""
    search_url = f"https://www.iplant.cn/info/{latin_name}"

    try:
        response = requests.get(search_url, headers=get_headers())
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 检查是否找到植物
        if "找不到符合条件的数据" in response.text:
            return None, "植物未找到"

        # 提取中文名
        chinese_name_elem = soup.select_one(".infocname")
        chinese_name = chinese_name_elem.text.strip() if chinese_name_elem else ""

        # 提取科属信息 - 改进的方法
        family = ""
        genus = ""
        # 从分类树中提取科属信息
        class_sys_div = soup.select_one("#rightclasssys")
        if class_sys_div:
            # 查找科信息 - 通常在倒数第二层
            family_div = class_sys_div.find("div", text=lambda t: t and "科" in t if t else False)
            if family_div:
                family_link = family_div.find("a")
                if family_link:
                    family = family_link.text.strip()

            # 查找属信息 - 通常在最后一层之前
            genus_div = class_sys_div.find("div", text=lambda t: t and "属" in t if t else False)
            if genus_div:
                genus_link = genus_div.find("a")
                if genus_link:
                    genus = genus_link.text.strip()

        # 提取形态特征
        description = ""
        morphology_table = soup.select_one("#cont_mp11 table.t2")
        if morphology_table:
            rows = morphology_table.find_all("tr")
            for row in rows:
                feature = row.select_one(".td1 span")
                value = row.select_one(".td2 span")
                if feature and value:
                    description += f"{feature.text.strip()}：{value.text.strip()}; "

        # 提取生态习性
        ecology = ""
        ecology_table = soup.select_one("#cont_mp12 table.t2")
        if ecology_table:
            rows = ecology_table.find_all("tr")
            for row in rows:
                feature = row.select_one(".td1 span")
                value = row.select_one(".td2 span")
                if feature and value:
                    ecology += f"{feature.text.strip()}：{value.text.strip()}; "

        # 提取功用价值
        plant_usage = ""
        usage_table = soup.select_one("#cont_mp20 table.t2")
        if usage_table:
            rows = usage_table.find_all("tr")
            for row in rows:
                feature = row.select_one(".td1 span")
                value = row.select_one(".td2 span")
                if feature and value:
                    plant_usage += f"{feature.text.strip()}：{value.text.strip()}; "

        # 提取图片URL
        image_url = ""
        img_div = soup.select_one("#imglist")
        if img_div:
            img_tag = img_div.find("img")
            if img_tag and 'src' in img_tag.attrs:
                image_url = img_tag['src']
                # 确保URL是完整的
                if image_url.startswith("//"):
                    image_url = "https:" + image_url

        # 判断数据完整性
        complete_flag = bool(chinese_name and family and genus and description)

        # 收集数据
        plant_data = {
            "latin_name": latin_name,
            "chinese_name": chinese_name,
            "family": family,
            "genus": genus,
            "description": description.strip(),
            "ecology": ecology.strip(),
            "plant_usage": plant_usage.strip(),
            "image_url": image_url,
            "complete_flag": complete_flag
        }

        return plant_data, None

    except requests.exceptions.HTTPError as err:
        return None, f"HTTP错误: {err}"
    except requests.exceptions.ConnectionError as err:
        return None, f"连接错误: {err}"
    except requests.exceptions.Timeout as err:
        return None, f"超时错误: {err}"
    except requests.exceptions.RequestException as err:
        return None, f"请求错误: {err}"
    except Exception as err:
        return None, f"未知错误: {err}"


# 在数据库中插入或更新植物数据
def insert_plant_data(conn, plant_data):
    if not plant_data:
        return False

    cursor = conn.cursor()

    # 检查是否已存在
    cursor.execute("SELECT id, complete_flag FROM plants WHERE latin_name = %s", (plant_data["latin_name"],))
    result = cursor.fetchone()

    try:
        if result:
            # 如果现有记录已经是完整的，而新数据不完整，则保留原有数据
            existing_id, existing_complete = result
            if existing_complete == 1 and plant_data["complete_flag"] == 0:
                print(f"保留已有的完整数据: {plant_data['latin_name']}")
                return True

            # 更新现有记录
            sql = """
            UPDATE plants SET 
                chinese_name = %s,
                family = %s,
                genus = %s,
                description = %s,
                ecology = %s,
                plant_usage = %s,
                image_url = %s,
                complete_flag = %s
            WHERE latin_name = %s
            """
            cursor.execute(sql, (
                plant_data["chinese_name"],
                plant_data["family"],
                plant_data["genus"],
                plant_data["description"],
                plant_data["ecology"],
                plant_data["plant_usage"],
                plant_data["image_url"],
                plant_data["complete_flag"],
                plant_data["latin_name"]
            ))
            print(f"更新植物 {plant_data['latin_name']} 的信息")
        else:
            # 插入新记录
            sql = """
            INSERT INTO plants (
                latin_name, chinese_name, family, 
                genus, description, ecology, 
                plant_usage, image_url, complete_flag
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                plant_data["latin_name"],
                plant_data["chinese_name"],
                plant_data["family"],
                plant_data["genus"],
                plant_data["description"],
                plant_data["ecology"],
                plant_data["plant_usage"],
                plant_data["image_url"],
                plant_data["complete_flag"]
            ))
            print(f"添加新植物 {plant_data['latin_name']} 到数据库")

        conn.commit()
        return True
    except Exception as e:
        print(f"数据库操作错误: {str(e)}")
        conn.rollback()
        return False


# 保存未完整处理的植物列表，以便后续补充
def save_incomplete_plants(incomplete_plants):
    with open("incomplete_plants.json", "w", encoding="utf-8") as f:
        json.dump(incomplete_plants, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(incomplete_plants)} 个信息不完整的植物到 incomplete_plants.json")


# 主函数
def main():
    # 获取植物文件夹列表
    plant_folder = "D:/PlantData/PlantImage"
    plant_latin_names = [folder for folder in os.listdir(plant_folder)
                         if os.path.isdir(os.path.join(plant_folder, folder))]

    # 创建数据库连接
    conn = create_db_connection()
    if not conn:
        return

    # 创建表
    create_table(conn)

    # 统计信息
    total = len(plant_latin_names)
    success_count = 0
    error_count = 0
    incomplete_count = 0
    incomplete_plants = []

    # 记录处理进度
    log_file = "plant_scraping_log.txt"
    processed_plants = set()
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            processed_plants = set(line.strip() for line in f)

    log_handle = open(log_file, "a", encoding="utf-8")

    try:
        # 使用tqdm添加进度条
        for latin_name in tqdm(plant_latin_names, desc="爬取植物数据"):
            # 跳过已处理的植物
            if latin_name in processed_plants:
                print(f"跳过已处理: {latin_name}")
                continue

            print(f"\n正在处理: {latin_name}")

            # 爬取植物数据
            plant_data, error = scrape_plant_data(latin_name)

            if plant_data:
                if insert_plant_data(conn, plant_data):
                    success_count += 1
                    log_handle.write(f"{latin_name}\n")
                    log_handle.flush()

                    # 检查数据完整性
                    if plant_data["complete_flag"] == 0:
                        incomplete_count += 1
                        incomplete_plants.append({
                            "latin_name": latin_name,
                            "chinese_name": plant_data.get("chinese_name", ""),
                            "family": plant_data.get("family", ""),
                            "genus": plant_data.get("genus", "")
                        })

                    # 打印简要信息
                    print(f"植物: {latin_name}")
                    print(f"中文名: {plant_data.get('chinese_name', '暂无')}")
                    print(f"科属: {plant_data.get('family', '暂无')} / {plant_data.get('genus', '暂无')}")
                    print(f"数据完整性: {'完整' if plant_data.get('complete_flag') == 1 else '不完整'}")
                    print("-" * 50)
                else:
                    error_count += 1
            else:
                # 如果无法从iPlant获取数据，则添加一个基本记录
                basic_data = {
                    "latin_name": latin_name,
                    "chinese_name": "",
                    "common_name": "",
                    "family": "",
                    "genus": "",
                    "description": "",
                    "ecology": "",
                    "plant_usage": "",
                    "image_url": f"https://appdevplantassets.obs.cn-north-4.myhuaweicloud.com/BaiCao/{latin_name}.jpg",
                    "data_source": "基本信息",
                    "complete_flag": 0
                }

                if insert_plant_data(conn, basic_data):
                    success_count += 1
                    incomplete_count += 1
                    log_handle.write(f"{latin_name}\n")
                    log_handle.flush()

                    incomplete_plants.append({
                        "latin_name": latin_name,
                        "chinese_name": "",
                        "family": "",
                        "genus": ""
                    })

                    print(f"植物: {latin_name}")
                    print(f"状态: 仅保存基本信息")
                    print("-" * 50)
                else:
                    error_count += 1

            # 添加延时，避免请求过快
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n用户中断爬取过程。")
    except Exception as e:
        print(f"爬取过程中发生错误: {str(e)}")
    finally:
        # 保存不完整的植物列表
        save_incomplete_plants(incomplete_plants)

        # 关闭日志文件
        log_handle.close()

        # 关闭数据库连接
        conn.close()

        # 打印统计信息
        print("\n爬取结束!")
        print(f"总计植物: {total}")
        print(f"成功: {success_count}")
        print(f"失败: {error_count}")
        print(f"信息不完整: {incomplete_count}")
        print(f"已处理: {len(processed_plants)}")


if __name__ == "__main__":
    main()