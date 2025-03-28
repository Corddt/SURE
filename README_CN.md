[![PWC](https://img.shields.io/endpoint.svg?url=https://paperswithcode.com/badge/sure-survey-recipes-for-building-reliable-and/learning-with-noisy-labels-on-animal)](https://paperswithcode.com/sota/learning-with-noisy-labels-on-animal?p=sure-survey-recipes-for-building-reliable-and) [![PWC](https://img.shields.io/endpoint.svg?url=https://paperswithcode.com/badge/sure-survey-recipes-for-building-reliable-and/image-classification-on-food-101n-1)](https://paperswithcode.com/sota/image-classification-on-food-101n-1?p=sure-survey-recipes-for-building-reliable-and)


[![PWC](https://img.shields.io/endpoint.svg?url=https://paperswithcode.com/badge/sure-survey-recipes-for-building-reliable-and/long-tail-learning-on-cifar-10-lt-r-50)](https://paperswithcode.com/sota/long-tail-learning-on-cifar-10-lt-r-50?p=sure-survey-recipes-for-building-reliable-and)       [![PWC](https://img.shields.io/endpoint.svg?url=https://paperswithcode.com/badge/sure-survey-recipes-for-building-reliable-and/long-tail-learning-on-cifar-10-lt-r-10)](https://paperswithcode.com/sota/long-tail-learning-on-cifar-10-lt-r-10?p=sure-survey-recipes-for-building-reliable-and) 

[English](README.md) | [中文](README_CN.md)

# 📝 SURE (CVPR 2024 & ECCV 2024 OOD-CV 挑战赛冠军)

### 简介
这是我们CVPR 2024论文 *"SURE: SUrvey REcipes for building reliable and robust deep networks"* 的官方实现。我们的方法是解决现实世界挑战的强大工具，如长尾分类、带噪声标签学习、数据损坏和分布外检测。


[![arXiv](https://img.shields.io/badge/arXiv-2403.00543-red.svg)](https://openaccess.thecvf.com/content/CVPR2024/papers/Li_SURE_SUrvey_REcipes_for_building_reliable_and_robust_deep_networks_CVPR_2024_paper.pdf) 
[![Winner](https://img.shields.io/badge/Winner-ECCV%202024%20OOD--CV%20Challenge-yellow?style=flat)](https://www.ood-cv.org/challenge.html)


[![Project Page](https://img.shields.io/badge/项目主页-blue?style=flat)](https://yutingli0606.github.io/SURE/)
[![Google Drive](https://img.shields.io/badge/谷歌云盘-blue?style=flat)](https://drive.google.com/drive/folders/1xT-cX22_I8h5yAYT1WNJmhSLrQFZZ5t1?usp=sharing)
[![Poster](https://img.shields.io/badge/海报-blue?style=flat)](img/poster.pdf)

### 新闻
- **2024.09.26 :**  🏆 🏆 🏆 我们的工作在[ECCV 2024 OOD-CV挑战赛](https://www.ood-cv.org/challenge.html)中获得**第一名**！有关我们解决方案的更多详情，请参阅[SSB-OSR](https://github.com/LIYangggggg/SSB-OSR)代码库。
- **2024.02.27 :** :rocket: :rocket: :rocket: 我们的论文已被CVPR 2024接收！ 
<p align="center">
<img src="img/Teaser.png" width="1000px" alt="teaser">
</p>

## 目录
* [1. 方法概述](#1-方法概述)
* [2. 可视化结果](#2-可视化结果)
* [3. 安装](#3-安装)
* [4. 快速开始](#4-快速开始)
* [5. 引用](#5-引用)
* [6. 致谢](#6-致谢)

## 1. 方法概述
<p align="center">
<img src="img/recipes.png" width="1000px" alt="method">
</p>

## 2. 可视化结果
<p align="center">
<img src="img/confidence.png" width="1000px" alt="method">
</p>
<p align="center">
<img src="img/ood.png" width="650px" alt="method">
</p>

## 3. 安装

### 3.1. 环境

我们的模型可以在**单个 GPU RTX-4090 24G**上训练

```bash
conda env create -f environment.yml
conda activate u
```

代码在 Python 3.9 和 PyTorch 1.13.0 上测试通过。

### 3.2. 数据集
#### 3.2.1 CIFAR 和 Tiny-ImageNet
* 使用 **CIFAR10, CIFAR100 和 Tiny-ImageNet** 进行失败预测（也称为误分类检测）。
* 我们保留 **10%** 的训练样本作为失败预测的验证数据集。
* 将数据集下载到 ./data/ 并分割为 train/val/test。
以 CIFAR10 为例：
```
cd data
bash download_cifar.sh
```
文件结构应如下所示：
```
./data/CIFAR10/
├── train
├── val
└── test
```
* 我们已经分割好了 Tiny-imagenet，你可以从[这里](https://drive.google.com/drive/folders/1xT-cX22_I8h5yAYT1WNJmhSLrQFZZ5t1?usp=sharing)下载。

#### 3.2.2 ImageNet1k 和 ImageNet21k
* 使用 **ImageNet1k 和 ImageNet21k** 进行分布外样本检测。
* 对于 ImageNet，ImageNet-1K 类别（ILSVRC12 挑战赛）被用作已知类别，而从 [ImageNet-21K-P](https://arxiv.org/abs/2104.10972) 中选择的特定类别被用作未知类别。
有关数据集准备的更多详情，请参阅[这里](https://github.com/sgvaze/SSB/blob/main/DATA.md)。

#### 3.2.3 Animal-10N 和 Food-101N
* 使用 **Animal-10N 和 Food-101N** 进行带噪声标签的学习。
* 要下载 Animal-10N 数据集 [[Song et al., 2019]](https://proceedings.mlr.press/v97/song19b/song19b.pdf)，请参阅[这里](https://dm.kaist.ac.kr/datasets/animal-10n/)。文件结构应如下所示：
```
./data/Animal10N/
├── train
└── test
```
* 要下载 Food-101N 数据集 [[Lee et al., 2018]](https://arxiv.org/pdf/1711.07131.pdf)，请参阅[这里](https://kuanghuei.github.io/Food-101N/)。文件结构应如下所示：
```
./data/Food-101N/
├── train
└── test
```

#### 3.2.4 CIFAR-LT
* 使用不平衡因子（10, 50, 100）的 **CIFAR-LT** 进行长尾分类。
* 将原始 CIFAR10 和 CIFAR100（不要分割成验证集）重命名为 'CIFAR10_LT' 和 'CIFAR100_LT'。
* 文件结构应如下所示：
```
./data/CIFAR10_LT/
├── train
└── test
```

#### 3.2.5 CIFAR10-C
* 使用 **CIFAR10-C** 测试数据损坏下的鲁棒性。
* 要下载 CIFAR10-C 数据集 [[Hendrycks et al., 2019]](https://arxiv.org/pdf/1903.12261.pdf)，请参阅[这里](https://github.com/hendrycks/robustness?tab=readme-ov-file)。文件结构应如下所示：
```
./data/CIFAR-10-C/
├── brightness.npy
├── contrast.npy
├── defocus_blur.npy
...
```

#### 3.2.6 Stanford CARS
* 我们还在 **Stanford CARS** 上进行了实验，该数据集包含 196 个类别的 16,185 张汽车图像。数据被分为 8,144 张训练图像和 8,041 张测试图像。
* 要下载该数据集，请参阅[这里](http://ai.stanford.edu/~jkrause/cars/car_dataset.html)。文件结构应如下所示：
```
./data/CARS/
├── train
└── test 
...
```

## 4. 快速开始

```bash
conda env create -f environment.yml
conda activate u
```

### 4.1 失败预测
* 我们在 ./run/ 中提供了方便全面的命令，用于在不同数据集上训练和测试不同的骨干网络，帮助研究人员重现论文中的结果。

<details>
<summary>
以 run/CIFAR10/deit.sh 为例：

</summary>
  <details>
   <summary>
    MSP
   </summary>
    
      python3 main.py \
      --batch-size 64 \
      --gpu 5 \
      --epochs 50 \
      --lr 0.01 \
      --weight-decay 5e-5 \
      --nb-run 3 \
      --model-name deit \
      --optim-name baseline \
      --crl-weight 0 \
      --mixup-weight 0 \
      --mixup-beta 10 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10
      
      python3 test.py \
      --batch-size 64 \
      --gpu 5 \
      --nb-run 3 \
      --model-name deit \
      --optim-name baseline \
      --crl-weight 0 \
      --mixup-weight 0 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10
  </details>

  <details>
   <summary>
    RegMixup
   </summary>
    

      python3 main.py \
      --batch-size 64 \
      --gpu 5 \
      --epochs 50 \
      --lr 0.01 \
      --weight-decay 5e-5 \
      --nb-run 3 \
      --model-name deit \
      --optim-name baseline \
      --crl-weight 0 \
      --mixup-weight 0.2 \
      --mixup-beta 10 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10
      
      python3 test.py \
      --batch-size 64 \
      --gpu 5 \
      --nb-run 3 \
      --model-name deit \
      --optim-name baseline \
      --crl-weight 0 \
      --mixup-weight 0.2 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10

  </details>
  <details>
   <summary>
    CRL
   </summary>
    


     python3 main.py \
     --batch-size 64 \
     --gpu 5 \
     --epochs 50 \
     --lr 0.01 \
     --weight-decay 5e-5 \
     --nb-run 3 \
     --model-name deit \
     --optim-name baseline \
     --crl-weight 0.2 \
     --mixup-weight 0 \
     --mixup-beta 10 \
     --save-dir ./CIFAR10_out/deit_out \
     Cifar10
     
     python3 test.py \
     --batch-size 64 \
     --gpu 5 \
     --nb-run 3 \
     --model-name deit \
     --optim-name baseline \
     --crl-weight 0.2 \
     --mixup-weight 0 \
     --save-dir ./CIFAR10_out/deit_out \
     Cifar10

  </details>
  <details>
   <summary>
    SAM
   </summary>
    

      python3 main.py \
      --batch-size 64 \
      --gpu 5 \
      --epochs 50 \
      --lr 0.01 \
      --weight-decay 5e-5 \
      --nb-run 3 \
      --model-name deit \
      --optim-name sam \
      --crl-weight 0 \
      --mixup-weight 0 \
      --mixup-beta 10 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10
      
      python3 test.py \
      --batch-size 64 \
      --gpu 5 \
      --nb-run 3 \
      --model-name deit \
      --optim-name sam \
      --crl-weight 0 \
      --mixup-weight 0 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10

  </details>
  <details>
   <summary>
    SWA
   </summary>
    

      python3 main.py \
      --batch-size 64 \
      --gpu 5 \
      --epochs 50 \
      --lr 0.01 \
      --weight-decay 5e-5 \
      --swa-epoch-start 0 \
      --swa-lr 0.004 \
      --nb-run 3 \
      --model-name deit \
      --optim-name swa \
      --crl-weight 0 \
      --mixup-weight 0 \
      --mixup-beta 10 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10
      
      python3 test.py \
      --batch-size 64 \
      --gpu 5 \
      --nb-run 3 \
      --model-name deit \
      --optim-name swa \
      --crl-weight 0 \
      --mixup-weight 0 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10

  </details>
  <details>
   <summary>
    FMFP
   </summary>
    

      python3 main.py \
      --batch-size 64 \
      --gpu 5 \
      --epochs 50 \
      --lr 0.01 \
      --weight-decay 5e-5 \
      --swa-epoch-start 0 \
      --swa-lr 0.004 \
      --nb-run 3 \
      --model-name deit \
      --optim-name fmfp \
      --crl-weight 0 \
      --mixup-weight 0 \
      --mixup-beta 10 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10
      
      python3 test.py \
      --batch-size 64 \
      --gpu 5 \
      --nb-run 3 \
      --model-name deit \
      --optim-name fmfp \
      --crl-weight 0 \
      --mixup-weight 0 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10


  </details>
  <details>
   <summary>
    SURE
   </summary>
    

      python3 main.py \
      --batch-size 64 \
      --gpu 5 \
      --epochs 50 \
      --lr 0.01 \
      --weight-decay 5e-5 \
      --swa-epoch-start 0 \
      --swa-lr 0.004 \
      --nb-run 3 \
      --model-name deit \
      --optim-name fmfp \
      --crl-weight 0 \
      --mixup-weight 0.2 \
      --mixup-beta 10 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10
      
      python3 test.py \
      --batch-size 64 \
      --gpu 5 \
      --nb-run 3 \
      --model-name deit \
      --optim-name fmfp \
      --crl-weight 0 \
      --mixup-weight 0.2 \
      --save-dir ./CIFAR10_out/deit_out \
      Cifar10
  </details>
</details>


<details>
<summary>
失败预测的结果。
</summary>
<p align="center">
<img src="img/main_results.jpeg" width="1000px" alt="method">
</p>
</details>


### 4.2 长尾分类
* 我们在 ./run/CIFAR10_LT 和 ./run/CIFAR100_LT 中提供了方便全面的命令，用于在长尾分布下训练和测试我们的方法。

<details>
<summary>
以 run/CIFAR10_LT/resnet32.sh 为例：

</summary>
  <details>
   <summary>
    不平衡因子=10
   </summary>
    
      python3 main.py \
      --batch-size 128 \
      --gpu 0 \
      --epochs 200 \
      --nb-run 3 \
      --model-name resnet32 \
      --optim-name fmfp \
      --crl-weight 0 \
      --mixup-weight 1 \
      --mixup-beta 10 \
      --use-cosine \
      --save-dir ./CIFAR10_LT/res32_out \
      Cifar10_LT
      
      python3 test.py \
      --batch-size 128 \
      --gpu 0 \
      --nb-run 3 \
      --model-name resnet32 \
      --optim-name fmfp \
      --crl-weight 0 \
      --mixup-weight 1 \
      --use-cosine \
      --save-dir ./CIFAR10_LT/res32_out \
      Cifar10_LT
  </details>

  <details>
   <summary>
    不平衡因子 = 50
   </summary>
    
      python3 main.py \
      --batch-size 128 \
      --gpu 0 \
      --epochs 200 \
      --nb-run 3 \
      --model-name resnet32 \
      --optim-name fmfp \
      --crl-weight 0 \
      --mixup-weight 1 \
      --mixup-beta 10 \
      --use-cosine \
      --save-dir ./CIFAR10_LT_50/res32_out \
      Cifar10_LT_50
      
      python3 test.py \
      --batch-size 128 \
      --gpu 0 \
      --nb-run 3 \
      --model-name resnet32 \
      --optim-name fmfp \
      --crl-weight 0 \
      --mixup-weight 1 \
      --use-cosine \
      --save-dir ./CIFAR10_LT_50/res32_out \
      Cifar10_LT_50
      
  </details>
  
  <details>
   <summary>
    不平衡因子 = 100
   </summary>
   
    python3 main.py \
    --batch-size 128 \
    --gpu 0 \
    --epochs 200 \
    --nb-run 3 \
    --model-name resnet32 \
    --optim-name fmfp \
    --crl-weight 0 \
    --mixup-weight 1 \
    --mixup-beta 10 \
    --use-cosine \
    --save-dir ./CIFAR10_LT_100/res32_out \
    Cifar10_LT_100
    
    python3 test.py \
    --batch-size 128 \
    --gpu 0 \
    --nb-run 3 \
    --model-name resnet32 \
    --optim-name fmfp \
    --crl-weight 0 \
    --mixup-weight 1 \
    --use-cosine \
    --save-dir ./CIFAR10_LT_100/res32_out \
    Cifar10_LT_100
  </details>
</details>

你可以通过以下方式进行第二阶段的不确定性感知重加权：
```
python3 finetune.py \
--batch-size 128 \
--gpu 5 \
--nb-run 1 \
--model-name resnet32 \
--optim-name fmfp \
--fine-tune-lr 0.005 \
--reweighting-type exp \
--t 1 \
--crl-weight 0 \
--mixup-weight 1 \
--mixup-beta 10 \
--fine-tune-epochs 50 \
--use-cosine \
--save-dir ./CIFAR100LT_100_out/51.60 \
Cifar100_LT_100
```

<details>
<summary>
长尾分类的结果。
</summary>
<p align="center">
<img src="img/long-tail.jpeg" width="600px" alt="method">
</p>
</details>

### 4.3 带噪声标签的学习
* 我们在 ./run/animal10N 和 ./run/Food101N 中提供了方便全面的命令，用于使用带噪声标签训练和测试我们的方法。

<details>
   
   <summary>
    Animal-10N
   </summary>  
   
     python3 main.py \
     --batch-size 128 \
     --gpu 0 \
     --epochs 200 \
     --nb-run 1 \
     --model-name vgg19bn \
     --optim-name fmfp \
     --crl-weight 0.2 \
     --mixup-weight 1 \
     --mixup-beta 10 \
     --use-cosine \
     --save-dir ./Animal10N_out/vgg19bn_out \
     Animal10N
     
     python3 test.py \
     --batch-size 128 \
     --gpu 0 \
     --nb-run 1 \
     --model-name vgg19bn \
     --optim-name baseline \
     --crl-weight 0.2 \
     --mixup-weight 1 \
     --use-cosine \
     --save-dir ./Animal10N_out/vgg19bn_out \
     Animal10N

  </details>
  <details>
   <summary>
    Food-101N
   </summary>
    

     python3 main.py \
     --batch-size 64 \
     --gpu 0 \
     --epochs 30 \
     --nb-run 1 \
     --model-name resnet50 \
     --optim-name fmfp \
     --crl-weight 0.2 \
     --mixup-weight 1 \
     --mixup-beta 10 \
     --lr 0.01 \
     --swa-lr 0.005 \
     --swa-epoch-start 22 \
     --use-cosine True \
     --save-dir ./Food101N_out/resnet50_out \
     Food101N
     
     python3 test.py \
     --batch-size 64 \
     --gpu 0 \
     --nb-run 1 \
     --model-name resnet50 \
     --optim-name fmfp \
     --crl-weight 0.2 \
     --mixup-weight 1 \
     --use-cosine True \
     --save-dir ./Food101N_out/resnet50_out \
     Food101N

  </details>

  
<details>
<summary>
带噪声标签学习的结果。
</summary>
<p align="center">
<img src="img/label-noise.jpeg" width="600px" alt="method">
</p>
</details> 


### 4.4 数据损坏下的鲁棒性
* 你可以通过以下代码在 test.py 中测试 CIFAR10-C：
```
if args.data_name == 'cifar10':
    cor_results_storage = test_cifar10c_corruptions(net, args.corruption_dir, transform_test,
                                                    args.batch_size, metrics, logger)
    cor_results = {corruption: {
                   severity: {
                   metric: cor_results_storage[corruption][severity][metric][0] for metric in metrics} for severity
                   in range(1, 6)} for corruption in data.CIFAR10C.CIFAR10C.cifarc_subsets}
    cor_results_all_models[f"model_{r + 1}"] = cor_results
``` 
* 结果保存在 cifar10c_results.csv 中。
* 测试 CIFAR10-C 需要一段时间。如果你不需要结果，只需注释掉该代码。

<details>
<summary>
分布偏移下的失败预测结果。
</summary>
<p align="center">
<img src="img/data-corruption.jpeg" width="1000px" alt="method">
</p>
</details>

### 4.5 分布外检测
* 你可以通过 [SSB-OSR](https://github.com/LIYangggggg/SSB-OSR) 在 ImageNet 上进行测试。

<details>
<summary>
分布外检测的结果。
</summary>
<p align="center">
<img src="img/ood_results.png" width="800px" alt="method">
</p>
</details>

## 5. 引用
如果我们的项目对您的研究有帮助，请考虑引用：
```
@InProceedings{Li_2024_CVPR,
    author    = {Li, Yuting and Chen, Yingyi and Yu, Xuanlong and Chen, Dexiong and Shen, Xi},
    title     = {SURE: SUrvey REcipes for building reliable and robust deep networks},
    booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
    month     = {June},
    year      = {2024},
    pages     = {17500-17510}
}

@article{Li2024sureood,
    author    = {Li, Yang and Sha, Youyang and Wu, Shengliang and Li, Yuting and Yu, Xuanlong and Huang, Shihua and Cun, Xiaodong and Chen,Yingyi and Chen, Dexiong and Shen, Xi},
    title     = {SURE-OOD: Detecting OOD samples with SURE},
    month     = {September}
    year      = {2024},
}
```

## 6. 致谢
我们参考了 [FMFP](https://github.com/Impression2805/FMFP) 和 [OpenMix](https://github.com/Impression2805/OpenMix) 的代码。感谢他们的优秀工作。
