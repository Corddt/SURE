import os

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import numpy as np

# 指定数据集根目录
root_dir = "D:/PlantData/PlantImage"

# 存储每个类别的样本数量
class_counts = {}

# 遍历所有类别文件夹
for class_name in os.listdir(root_dir):
    class_path = os.path.join(root_dir, class_name)
    if os.path.isdir(class_path):
        # 计算该类别的图像文件数量（假设图像格式为jpg或png）
        image_count = len([f for f in os.listdir(class_path) 
                          if f.endswith('.jpg') or f.endswith('.png')])
        class_counts[class_name] = image_count

# 找出最大和最小样本数
max_samples = max(class_counts.values())
min_samples = min(class_counts.values())

# 计算不平衡因子
imbalance_factor = max_samples / min_samples

print(f"最大样本数: {max_samples}")
print(f"最小样本数: {min_samples}")
print(f"不平衡因子: {imbalance_factor}")

# 设置目标不平衡因子为100
target_imbalance_factor = 100

# 设置上限和下限
upper_limit = min_samples * target_imbalance_factor  # 400
lower_limit = max_samples / target_imbalance_factor  # 约92，放宽为40
lower_limit = 40
lower_limit = max(40, lower_limit)  # 取较大值

print(f"\n目标不平衡因子: {target_imbalance_factor}")
print(f"计算的上限: {upper_limit}")
print(f"计算的下限: {lower_limit}")

# 统计受影响的类别数和图像数
classes_above_limit = 0
images_above_limit = 0
images_to_reduce = 0

classes_below_limit = 0
images_below_limit = 0
images_to_generate = 0

for class_name, count in class_counts.items():
    # 统计超过上限的类别
    if count > upper_limit:
        classes_above_limit += 1
        images_above_limit += count
        images_to_reduce += (count - upper_limit)
    
    # 统计低于下限的类别
    if count < lower_limit:
        classes_below_limit += 1
        images_below_limit += count
        images_to_generate += (lower_limit - count)

# 统计结果
total_classes = len(class_counts)
total_images = sum(class_counts.values())

print(f"\n===== 上限设置影响分析 =====")
print(f"超过上限({upper_limit})的类别数: {classes_above_limit} ({classes_above_limit/total_classes*100:.2f}%)")
print(f"这些类别包含的图像总数: {images_above_limit} ({images_above_limit/total_images*100:.2f}%)")
print(f"需要减少的图像数: {images_to_reduce} ({images_to_reduce/total_images*100:.2f}%)")

print(f"\n===== 下限提升影响分析 =====")
print(f"低于下限({lower_limit})的类别数: {classes_below_limit} ({classes_below_limit/total_classes*100:.2f}%)")
print(f"这些类别包含的图像总数: {images_below_limit} ({images_below_limit/total_images*100:.2f}%)")
print(f"需要生成的图像数: {images_to_generate} ({images_to_generate/images_below_limit*100:.2f}% 增长)")

# 计算理论上的新不平衡因子
new_min = lower_limit
new_max = upper_limit
new_imbalance_factor = new_max / new_min
print(f"\n理论上的新不平衡因子: {new_imbalance_factor}")

# 可视化类别分布
plt.figure(figsize=(15, 8))
plt.bar(class_counts.keys(), class_counts.values())
plt.axhline(y=upper_limit, color='r', linestyle='-', label=f'上限 ({upper_limit})')
plt.axhline(y=lower_limit, color='g', linestyle='-', label=f'下限 ({lower_limit})')
plt.xticks(rotation=90)
plt.xlabel('植物类别')
plt.ylabel('样本数量')
plt.title('PlantImage 数据集类别分布')
plt.legend()
plt.tight_layout()
plt.savefig('class_distribution_with_limits.png')

# 绘制样本数量分布直方图
plt.figure(figsize=(12, 6))
counts = list(class_counts.values())
bins = np.logspace(np.log10(min(counts)), np.log10(max(counts)), 50)
plt.hist(counts, bins=bins)
plt.axvline(x=upper_limit, color='r', linestyle='-', label=f'上限 ({upper_limit})')
plt.axvline(x=lower_limit, color='g', linestyle='-', label=f'下限 ({lower_limit})')
plt.xscale('log')
plt.xlabel('样本数量')
plt.ylabel('类别数')
plt.title('样本数量分布直方图')
plt.legend()
plt.tight_layout()
plt.savefig('sample_count_histogram.png')

# 对样本数量排序
sorted_counts = sorted(class_counts.values())

# 计算每个可能的上限值对应的"受影响类别比例"和"受影响样本比例"
upper_candidates = []
for potential_upper in range(200, 1000, 50):  # 从200到1000，步长50
    classes_affected = sum(1 for count in sorted_counts if count > potential_upper)
    samples_affected = sum(count - potential_upper for count in sorted_counts if count > potential_upper)
    
    classes_ratio = classes_affected / total_classes
    samples_ratio = samples_affected / total_images
    
    # 计算一个"影响分数" - 越低越好
    impact_score = classes_ratio * 0.4 + samples_ratio * 0.6
    
    upper_candidates.append((potential_upper, impact_score, classes_affected, samples_affected))

# 计算每个可能的下限值对应的"受影响类别比例"和"需增强样本比例"
lower_candidates = []
for potential_lower in range(20, 100, 5):  # 从20到100，步长5
    classes_affected = sum(1 for count in sorted_counts if count < potential_lower)
    samples_to_add = sum(potential_lower - count for count in sorted_counts if count < potential_lower)
    
    classes_ratio = classes_affected / total_classes
    # 计算相对于现有样本的增长率
    growth_ratio = samples_to_add / sum(min(count, potential_lower) for count in sorted_counts if count < potential_lower)
    
    # 计算一个"影响分数" - 越低越好
    impact_score = classes_ratio * 0.3 + growth_ratio * 0.7
    
    lower_candidates.append((potential_lower, impact_score, classes_affected, samples_to_add))

# 找出影响分数最低的上限和下限
best_upper = min(upper_candidates, key=lambda x: x[1])
best_lower = min(lower_candidates, key=lambda x: x[1])

print(f"\n===== 最优上限分析 =====")
print(f"建议上限值: {best_upper[0]}")
print(f"影响分数: {best_upper[1]:.4f}")
print(f"影响类别数: {best_upper[2]} ({best_upper[2]/total_classes*100:.2f}%)")
print(f"需要减少样本数: {best_upper[3]} ({best_upper[3]/total_images*100:.2f}%)")

print(f"\n===== 最优下限分析 =====")
print(f"建议下限值: {best_lower[0]}")
print(f"影响分数: {best_lower[1]:.4f}")
print(f"影响类别数: {best_lower[2]} ({best_lower[2]/total_classes*100:.2f}%)")
print(f"需要增加样本数: {best_lower[3]}")

# 计算使用最优上下限后的理论不平衡因子
optimal_imbalance_factor = best_upper[0] / best_lower[0]
print(f"\n使用最优上下限后的理论不平衡因子: {optimal_imbalance_factor:.2f}")