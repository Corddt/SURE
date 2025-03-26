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
    "database": "plants_db"
}


# 创建数据库连接
def create_db_connection():
    try:
        conn = mysql.connector.connect(
            **DB_CONFIG,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
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
        ecology TEXT COMMENT '生长习性',
        plant_usage TEXT COMMENT '用途价值',
        image_url VARCHAR(255) COMMENT '图片URL',
        data_source VARCHAR(50) COMMENT '数据来源',
        complete_flag TINYINT DEFAULT 0 COMMENT '数据完整度标志: 0=不完整, 1=完整',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        INDEX idx_latin_name (latin_name),
        INDEX idx_chinese_name (chinese_name),
        INDEX idx_complete (complete_flag)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """)
    conn.commit()
    print("数据表已创建或已存在")


# 清理文本中的HTML标签
def clean_html(text):
    if text:
        # 移除HTML标签
        text = re.sub(r'<.*?>', '', text)
        # 移除多余空白字符
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    return ""


# 从iPlant网站抓取植物信息
def scrape_plant_data(latin_name, alternative_sources=True):
    search_url = f"https://www.iplant.cn/info/{quote(latin_name)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 检查是否有找到结果（如果页面包含"没有找到"等字样）
            if "没有找到" in response.text or "无结果" in response.text:
                print(f"iPlant没有找到植物: {latin_name}")
                # 尝试从其他来源获取
                if alternative_sources:
                    return try_alternative_sources(latin_name)
                return None

            # 提取中文名
            chinese_name = ""
            chinese_name_elem = soup.select_one(".infocname")
            if chinese_name_elem:
                chinese_name = chinese_name_elem.text.strip()

            # 提取俗名
            common_name = ""
            common_name_div = soup.select_one(".infomore")
            if common_name_div:
                common_name_text = common_name_div.text
                if "俗名：" in common_name_text:
                    common_name_match = re.search(r'俗名：(.*?)(?:异名|$)', common_name_text, re.DOTALL)
                    if common_name_match:
                        common_name = common_name_match.group(1).strip()

            # 获取形态特征
            description = ""
            morphology_section = soup.select_one("#info_mp11")
            if morphology_section:
                description_elements = morphology_section.select(".conten2 p")
                description = "\n".join([clean_html(p.text) for p in description_elements])

            # 获取生态习性
            ecology = ""
            ecology_section = soup.select_one("#info_mp12")
            if ecology_section:
                ecology_elements = ecology_section.select(".conten2 p")
                ecology = "\n".join([clean_html(p.text) for p in ecology_elements])

            # 获取功用价值
            usage = ""
            usage_section = soup.select_one("#info_mp20")
            if usage_section:
                usage_elements = usage_section.select(".conten2 p")
                usage = "\n".join([clean_html(p.text) for p in usage_elements])

            # 获取分类信息
            family = ""
            genus = ""
            taxonomy_section = soup.select_one("#info_mp21")
            if taxonomy_section:
                taxonomy_text = taxonomy_section.text
                family_match = re.search(r'科\s*[：:]\s*([^\n]+)', taxonomy_text)
                if family_match:
                    family = family_match.group(1).strip()

                genus_match = re.search(r'属\s*[：:]\s*([^\n]+)', taxonomy_text)
                if genus_match:
                    genus = genus_match.group(1).strip()

            # 构建图片URL
            image_url = f"https://appdevplantassets.obs.cn-north-4.myhuaweicloud.com/BaiCao/{latin_name}.jpg"

            # 检查数据完整性
            complete_flag = 1
            if not chinese_name or not family or not genus or not description:
                complete_flag = 0
                print(f"警告: {latin_name} 的信息不完整")

            # 返回所有提取的信息
            return {
                "latin_name": latin_name,
                "chinese_name": chinese_name,
                "common_name": common_name,
                "family": family,
                "genus": genus,
                "description": description,
                "ecology": ecology,
                "usage": usage,
                "image_url": image_url,
                "data_source": "iPlant",
                "complete_flag": complete_flag
            }
        else:
            print(f"访问{latin_name}页面时出错，状态码: {response.status_code}")
            if alternative_sources:
                return try_alternative_sources(latin_name)
            return None
    except Exception as e:
        print(f"抓取{latin_name}数据时发生错误: {str(e)}")
        if alternative_sources:
            return try_alternative_sources(latin_name)
        return None


# 尝试从其他来源获取植物信息
def try_alternative_sources(latin_name):
    # 1. 尝试从 POWO (Plants of the World Online) 获取
    print(f"尝试从POWO获取 {latin_name} 的信息...")

    try:
        # 使用POWO API或网页抓取
        powo_url = f"http://www.plantsoftheworldonline.org/taxon/{latin_name.replace(' ', '%20')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(powo_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取科和属信息
            family = ""
            genus = ""

            taxonomy_div = soup.select_one(".c-summary__list")
            if taxonomy_div:
                family_elem = taxonomy_div.find(string=re.compile("Family"))
                if family_elem and family_elem.find_parent():
                    family = family_elem.find_parent().find_next_sibling().text.strip()

                # 从拉丁名提取属
                genus = latin_name.split()[0] if " " in latin_name else ""

            # 提取描述
            description = ""
            description_div = soup.select_one(".c-taxon-description")
            if description_div:
                description = description_div.text.strip()

            # 构建图片URL
            image_url = f"https://appdevplantassets.obs.cn-north-4.myhuaweicloud.com/BaiCao/{latin_name}.jpg"

            return {
                "latin_name": latin_name,
                "chinese_name": "",  # POWO没有中文名
                "common_name": "",
                "family": family,
                "genus": genus,
                "description": description,
                "ecology": "",
                "usage": "",
                "image_url": image_url,
                "data_source": "POWO",
                "complete_flag": 0  # 标记为不完整
            }
    except Exception as e:
        print(f"从POWO获取数据失败: {str(e)}")

    # 2. 如果POWO也失败，仅保存拉丁名和图片URL
    print(f"无法获取 {latin_name} 的完整信息，仅保存基本数据")
    return {
        "latin_name": latin_name,
        "chinese_name": "",
        "common_name": "",
        "family": "",
        "genus": "",
        "description": "",
        "ecology": "",
        "usage": "",
        "image_url": f"https://appdevplantassets.obs.cn-north-4.myhuaweicloud.com/BaiCao/{latin_name}.jpg",
        "data_source": "基本信息",
        "complete_flag": 0  # 标记为不完整
    }


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
                common_name = %s,
                family = %s,
                genus = %s,
                description = %s,
                ecology = %s,
                plant_usage = %s,
                image_url = %s,
                data_source = %s,
                complete_flag = %s
            WHERE latin_name = %s
            """
            cursor.execute(sql, (
                plant_data["chinese_name"],
                plant_data["common_name"],
                plant_data["family"],
                plant_data["genus"],
                plant_data["description"],
                plant_data["ecology"],
                plant_data["usage"],
                plant_data["image_url"],
                plant_data["data_source"],
                plant_data["complete_flag"],
                plant_data["latin_name"]
            ))
            print(f"更新植物 {plant_data['latin_name']} 的信息")
        else:
            # 插入新记录
            sql = """
            INSERT INTO plants (
                latin_name, chinese_name, common_name, 
                family, genus, description, 
                ecology, plant_usage, image_url,
                data_source, complete_flag
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                plant_data["latin_name"],
                plant_data["chinese_name"],
                plant_data["common_name"],
                plant_data["family"],
                plant_data["genus"],
                plant_data["description"],
                plant_data["ecology"],
                plant_data["usage"],
                plant_data["image_url"],
                plant_data["data_source"],
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
        with open(log_file, "r") as f:
            processed_plants = set(line.strip() for line in f)

    log_handle = open(log_file, "a")

    try:
        # 使用tqdm添加进度条
        for latin_name in tqdm(plant_latin_names, desc="爬取植物数据"):
            # 跳过已处理的植物
            if latin_name in processed_plants:
                print(f"跳过已处理: {latin_name}")
                continue

            print(f"\n正在处理: {latin_name}")

            # 爬取植物数据
            plant_data = scrape_plant_data(latin_name)

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
                            "data_source": plant_data.get("data_source", "")
                        })

                    # 打印简要信息
                    print(f"植物: {latin_name}")
                    print(f"中文名: {plant_data.get('chinese_name', '暂无')}")
                    print(f"科属: {plant_data.get('family', '暂无')} / {plant_data.get('genus', '暂无')}")
                    print(f"数据来源: {plant_data.get('data_source', '未知')}")
                    print(f"数据完整性: {'完整' if plant_data.get('complete_flag') == 1 else '不完整'}")
                    print("-" * 50)
                else:
                    error_count += 1
            else:
                error_count += 1

            # 添加延时，避免请求过快
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n用户中断爬取过程。")
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