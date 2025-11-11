### To run the code using conda env
```bash
conda env -n <name> python=3.12
conda activate <name>
conda install jupyter ipykernel pandas matplotlib transformers sacremoses scikit-learn
```
last command you get from [Pytorch documentation](https://pytorch.org/get-started/locally/), in my case it was 
```bash
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu130
```