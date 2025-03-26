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
--save-dir ./PlantImage_out/resnet18_out \
PlantImage_Balanced_Split

python3 test.py \
--batch-size 128 \
--gpu 0 \
--nb-run 3 \
--model-name resnet32 \
--optim-name fmfp \
--crl-weight 0 \
--mixup-weight 1 \
--use-cosine \
--save-dir ./PlantImage_out/resnet18_out \
PlantImage_Balanced_Split