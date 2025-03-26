import os
import random
import shutil

import matplotlib
from PIL import Image, ImageEnhance, ImageOps
import numpy as np
import matplotlib.pyplot as plt
matplotlib.use('Agg')
from tqdm import tqdm
import time

# 配置参数
source_dir = "D:/PlantData/PlantImage"  # 原始数据集目录
target_dir = "D:/PlantData/PlantImage_Balanced"  # 新的平衡数据集目录
upper_limit = 950  # 最优上限
lower_limit = 20   # 最优下限
augmentation_techniques = ['rotate', 'flip', 'brightness', 'contrast', 'crop']  # 数据增强方法

# 创建目标目录
os.makedirs(target_dir, exist_ok=True)

# 存储类别统计信息
class_stats = {}

print("第1步：分析源数据集...")

# 统计每个类别的样本数量
class_counts = {}
for class_name in os.listdir(source_dir):
    class_path = os.path.join(source_dir, class_name)
    if os.path.isdir(class_path):
        image_files = [f for f in os.listdir(class_path) 
                       if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        class_counts[class_name] = len(image_files)

# 打印数据集统计信息
total_classes = len(class_counts)
total_images = sum(class_counts.values())
print(f"源数据集包含 {total_classes} 个类别，总共 {total_images} 张图像")

# 划分类别
above_limit = {k: v for k, v in class_counts.items() if v > upper_limit}
below_limit = {k: v for k, v in class_counts.items() if v < lower_limit}
within_limit = {k: v for k, v in class_counts.items() if lower_limit <= v <= upper_limit}

print(f"超过上限({upper_limit})的类别数: {len(above_limit)}")
print(f"低于下限({lower_limit})的类别数: {len(below_limit)}")
print(f"在范围内的类别数: {len(within_limit)}")

# 数据增强函数
def augment_image(img, technique):
    """对图像应用指定的增强技术"""
    if technique == 'rotate':
        angle = random.choice([-45, -30, -15, 15, 30, 45])
        return img.rotate(angle, expand=True, fillcolor=(255, 255, 255))
    
    elif technique == 'flip':
        if random.random() > 0.5:
            return ImageOps.mirror(img)
        else:
            return ImageOps.flip(img)
    
    elif technique == 'brightness':
        factor = random.uniform(0.8, 1.2)
        return ImageEnhance.Brightness(img).enhance(factor)
    
    elif technique == 'contrast':
        factor = random.uniform(0.8, 1.2)
        return ImageEnhance.Contrast(img).enhance(factor)
    
    elif technique == 'crop':
        width, height = img.size
        # 确保裁剪区域不小于原图的70%
        crop_ratio = random.uniform(0.7, 0.9)
        crop_width = int(width * crop_ratio)
        crop_height = int(height * crop_ratio)
        
        # 随机选择裁剪起点
        left = random.randint(0, width - crop_width)
        top = random.randint(0, height - crop_height)
        
        # 裁剪并调整回原始大小
        cropped = img.crop((left, top, left + crop_width, top + crop_height))
        return cropped.resize((width, height), Image.LANCZOS)
    
    return img

print("\n第2步：处理数据集...")

# 处理函数
def process_class(class_name, count):
    """处理单个类别，创建平衡后的版本"""
    src_path = os.path.join(source_dir, class_name)
    dst_path = os.path.join(target_dir, class_name)
    os.makedirs(dst_path, exist_ok=True)
    
    # 获取所有图像文件
    image_files = [f for f in os.listdir(src_path) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    stats = {
        "original_count": count,
        "sampled_count": 0,
        "augmented_count": 0,
        "final_count": 0
    }
    
    # 对于超过上限的类别，随机采样
    if count > upper_limit:
        selected_files = random.sample(image_files, upper_limit)
        for file in selected_files:
            src_file = os.path.join(src_path, file)
            dst_file = os.path.join(dst_path, file)
            shutil.copy2(src_file, dst_file)
        stats["sampled_count"] = upper_limit
        stats["final_count"] = upper_limit
    
    # 对于低于下限的类别，先复制所有现有图像，然后进行数据增强
    elif count < lower_limit:
        # 复制所有原始图像
        for file in image_files:
            src_file = os.path.join(src_path, file)
            dst_file = os.path.join(dst_path, file)
            shutil.copy2(src_file, dst_file)
        
        stats["sampled_count"] = count
        
        # 计算需要通过增强生成的图像数量
        augment_count = lower_limit - count
        
        # 数据增强
        augmentation_per_image = (augment_count // count) + 1
        
        aug_count = 0
        for file in image_files:
            if aug_count >= augment_count:
                break
                
            src_file = os.path.join(src_path, file)
            
            try:
                img = Image.open(src_file).convert('RGB')
                
                for i in range(augmentation_per_image):
                    if aug_count >= augment_count:
                        break
                    
                    # 随机选择1-3种增强技术组合
                    num_techniques = min(random.randint(1, 3), len(augmentation_techniques))
                    selected_techniques = random.sample(augmentation_techniques, num_techniques)
                    
                    # 应用所选增强技术
                    augmented_img = img.copy()
                    for technique in selected_techniques:
                        augmented_img = augment_image(augmented_img, technique)
                    
                    # 保存增强后的图像
                    file_name, ext = os.path.splitext(file)
                    aug_file = f"{file_name}_aug_{i}{ext}"
                    aug_path = os.path.join(dst_path, aug_file)
                    augmented_img.save(aug_path, quality=95)
                    
                    aug_count += 1
            
            except Exception as e:
                print(f"处理文件 {src_file} 时出错: {str(e)}")
        
        stats["augmented_count"] = aug_count
        stats["final_count"] = count + aug_count
    
    # 对于在范围内的类别，直接复制
    else:
        for file in image_files:
            src_file = os.path.join(src_path, file)
            dst_file = os.path.join(dst_path, file)
            shutil.copy2(src_file, dst_file)
        
        stats["sampled_count"] = count
        stats["final_count"] = count
    
    return stats

# 使用tqdm显示进度
with tqdm(total=total_classes) as pbar:
    for class_name, count in class_counts.items():
        class_stats[class_name] = process_class(class_name, count)
        pbar.update(1)

print("\n第3步：生成报告...")

# 统计处理后的结果
new_total_images = sum(stats["final_count"] for stats in class_stats.values())
max_count = max(stats["final_count"] for stats in class_stats.values())
min_count = min(stats["final_count"] for stats in class_stats.values())
new_imbalance_factor = max_count / min_count

# 绘制处理前后的对比图
plt.figure(figsize=(12, 8))

# 转换为列表，便于绘图
classes = list(class_counts.keys())
original_counts = [class_counts[cls] for cls in classes]
final_counts = [class_stats[cls]["final_count"] for cls in classes]

# 按处理后的样本数量排序
combined = list(zip(classes, original_counts, final_counts))
combined.sort(key=lambda x: x[2])  # 按处理后数量排序
classes, original_counts, final_counts = zip(*combined)

# 绘制排序后的数据
plt.plot(range(len(classes)), original_counts, 'r-', label='处理前')
plt.plot(range(len(classes)), final_counts, 'b-', label='处理后')
plt.axhline(y=upper_limit, color='r', linestyle='--', label=f'上限 ({upper_limit})')
plt.axhline(y=lower_limit, color='g', linestyle='--', label=f'下限 ({lower_limit})')

plt.yscale('log')
plt.xlabel('类别（按处理后数量排序）')
plt.ylabel('样本数量（对数刻度）')
plt.title('数据集处理前后对比')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(target_dir, 'before_after_comparison.png'))

# 生成处理摘要
summary = {
    "原始数据集": {
        "类别总数": total_classes,
        "图像总数": total_images,
        "最大样本数": max(class_counts.values()),
        "最小样本数": min(class_counts.values()),
        "不平衡因子": max(class_counts.values()) / min(class_counts.values())
    },
    "处理后数据集": {
        "类别总数": total_classes,
        "图像总数": new_total_images,
        "最大样本数": max_count,
        "最小样本数": min_count,
        "不平衡因子": new_imbalance_factor
    },
    "处理统计": {
        "超过上限类别数": len(above_limit),
        "低于下限类别数": len(below_limit),
        "在范围内类别数": len(within_limit),
        "减少的样本数": sum(class_counts[cls] - class_stats[cls]["final_count"] 
                        for cls in above_limit),
        "增加的样本数": sum(class_stats[cls]["augmented_count"] for cls in below_limit)
    }
}

# 将摘要保存为文本文件
with open(os.path.join(target_dir, 'processing_summary.txt'), 'w') as f:
    f.write("数据集处理摘要\n")
    f.write("=" * 50 + "\n\n")
    
    f.write("原始数据集:\n")
    for k, v in summary["原始数据集"].items():
        f.write(f"  {k}: {v}\n")
    
    f.write("\n处理后数据集:\n")
    for k, v in summary["处理后数据集"].items():
        f.write(f"  {k}: {v}\n")
    
    f.write("\n处理统计:\n")
    for k, v in summary["处理统计"].items():
        f.write(f"  {k}: {v}\n")

# 打印摘要
print("\n数据集处理完成！")
print(f"原始不平衡因子: {summary['原始数据集']['不平衡因子']:.2f}")
print(f"处理后不平衡因子: {summary['处理后数据集']['不平衡因子']:.2f}")
print(f"原始图像总数: {summary['原始数据集']['图像总数']}")
print(f"处理后图像总数: {summary['处理后数据集']['图像总数']}")
print(f"详细报告已保存至: {os.path.join(target_dir, 'processing_summary.txt')}")
print(f"对比图已保存至: {os.path.join(target_dir, 'before_after_comparison.png')}")