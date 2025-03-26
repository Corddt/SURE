import os
import shutil
import numpy as np
from tqdm import tqdm
from sklearn.model_selection import StratifiedShuffleSplit

# 设置路径
source_dir = "D:/PlantData/PlantImage_Balanced"
target_base_dir = "D:/PlantData/PlantImage_Balanced_Split"
train_dir = os.path.join(target_base_dir, "train")
test_dir = os.path.join(target_base_dir, "test")

# 创建目标目录
os.makedirs(target_base_dir, exist_ok=True)
os.makedirs(train_dir, exist_ok=True)
os.makedirs(test_dir, exist_ok=True)

def stratified_split_dataset():
    print("开始分层抽样划分数据集...")
    
    # 收集所有图像和标签
    all_files = []
    all_labels = []
    all_classes = []
    
    print("正在收集数据集信息...")
    for class_name in tqdm(os.listdir(source_dir)):
        class_dir = os.path.join(source_dir, class_name)
        if not os.path.isdir(class_dir):
            continue
            
        # 统计该类别下的所有图像
        all_classes.append(class_name)
        image_files = [f for f in os.listdir(class_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        # 为每个图像记录类别标签(使用类别索引作为标签)
        class_idx = len(all_classes) - 1
        for img_file in image_files:
            all_files.append((class_name, img_file))
            all_labels.append(class_idx)
    
    # 打印数据集基本统计信息
    print(f"数据集包含 {len(all_classes)} 个类别，共 {len(all_files)} 张图像")
    
    # 分析类别分布
    label_counts = {}
    for label in all_labels:
        label_counts[label] = label_counts.get(label, 0) + 1
    
    # 打印最大最小类别
    max_class_idx = max(label_counts, key=label_counts.get)
    min_class_idx = min(label_counts, key=label_counts.get)
    max_class_name = all_classes[max_class_idx]
    min_class_name = all_classes[min_class_idx]
    
    print(f"最大类别: {max_class_name} ({label_counts[max_class_idx]} 张图像)")
    print(f"最小类别: {min_class_name} ({label_counts[min_class_idx]} 张图像)")
    print(f"不平衡因子: {label_counts[max_class_idx]/label_counts[min_class_idx]:.2f}")
    
    # 使用分层抽样划分数据集(80%训练, 20%测试)
    print("执行分层抽样划分...")
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_indices, test_indices = next(sss.split(all_files, all_labels))
    
    # 为每个类别创建目录
    for class_name in all_classes:
        os.makedirs(os.path.join(train_dir, class_name), exist_ok=True)
        os.makedirs(os.path.join(test_dir, class_name), exist_ok=True)
    
    # 复制文件到训练集
    print("复制文件到训练集...")
    for idx in tqdm(train_indices):
        class_name, img_file = all_files[idx]
        source_file = os.path.join(source_dir, class_name, img_file)
        target_file = os.path.join(train_dir, class_name, img_file)
        shutil.copy2(source_file, target_file)
    
    # 复制文件到测试集
    print("复制文件到测试集...")
    for idx in tqdm(test_indices):
        class_name, img_file = all_files[idx]
        source_file = os.path.join(source_dir, class_name, img_file)
        target_file = os.path.join(test_dir, class_name, img_file)
        shutil.copy2(source_file, target_file)
    
    # 验证划分结果
    print("\n验证划分结果:")
    train_stats = {}
    test_stats = {}
    
    # 统计训练集和测试集中每个类别的数量
    for class_name in all_classes:
        train_class_dir = os.path.join(train_dir, class_name)
        test_class_dir = os.path.join(test_dir, class_name)
        
        train_count = len([f for f in os.listdir(train_class_dir) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
        test_count = len([f for f in os.listdir(test_class_dir) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
        
        train_stats[class_name] = train_count
        test_stats[class_name] = test_count
    
    total_train = sum(train_stats.values())
    total_test = sum(test_stats.values())
    
    print(f"总训练样本: {total_train}")
    print(f"总测试样本: {total_test}")
    print(f"训练集比例: {total_train/(total_train+total_test)*100:.2f}%")
    print(f"测试集比例: {total_test/(total_train+total_test)*100:.2f}%")
    
    # 检查一些类别的比例
    print("\n抽样类别验证:")
    for class_name in [all_classes[max_class_idx], all_classes[min_class_idx]]:
        class_total = train_stats[class_name] + test_stats[class_name]
        train_ratio = train_stats[class_name] / class_total
        test_ratio = test_stats[class_name] / class_total
        
        print(f"类别 '{class_name}':")
        print(f"  训练样本: {train_stats[class_name]} ({train_ratio*100:.2f}%)")
        print(f"  测试样本: {test_stats[class_name]} ({test_ratio*100:.2f}%)")
    
    print("\n数据集划分完成!")
    print(f"训练集保存在: {train_dir}")
    print(f"测试集保存在: {test_dir}")
    
    # 写入划分报告
    with open(os.path.join(target_base_dir, "split_report.txt"), "w") as f:
        f.write(f"数据集划分报告\n")
        f.write(f"====================\n\n")
        f.write(f"原始数据集: {source_dir}\n")
        f.write(f"总类别数: {len(all_classes)}\n")
        f.write(f"总图像数: {len(all_files)}\n\n")
        
        f.write(f"最大类别: {max_class_name} ({label_counts[max_class_idx]} 张图像)\n")
        f.write(f"最小类别: {min_class_name} ({label_counts[min_class_idx]} 张图像)\n")
        f.write(f"不平衡因子: {label_counts[max_class_idx]/label_counts[min_class_idx]:.2f}\n\n")
        
        f.write(f"训练集: {total_train} 张图像 ({total_train/(total_train+total_test)*100:.2f}%)\n")
        f.write(f"测试集: {total_test} 张图像 ({total_test/(total_train+total_test)*100:.2f}%)\n\n")
        
        f.write("每个类别的分布:\n")
        f.write("-----------------\n")
        for class_name in all_classes:
            class_total = train_stats[class_name] + test_stats[class_name]
            train_ratio = train_stats[class_name] / class_total
            test_ratio = test_stats[class_name] / class_total
            
            f.write(f"类别 '{class_name}':\n")
            f.write(f"  总样本: {class_total}\n")
            f.write(f"  训练样本: {train_stats[class_name]} ({train_ratio*100:.2f}%)\n")
            f.write(f"  测试样本: {test_stats[class_name]} ({test_ratio*100:.2f}%)\n\n")

if __name__ == "__main__":
    stratified_split_dataset()
