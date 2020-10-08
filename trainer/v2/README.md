# Is The Mountain Out? Trainer

## Getting Started

### Install Anaconda

Follow instructions at https://www.anaconda.com/products/individual/get-started

### Install Packages

Create a virtual environment named `tf_gpu` containing tensorflow including all cuda and cuDNN compatible versions.

```
conda create --name tf_gpu \
  python=3.8 \
  ipykernel \
  ipython_genutils \
  nbformat \
  pillow \
  pydot \
  graphviz \
  matplotlib \
  scikit-learn
conda activate tf_gpu
pip install tensorflow-gpu==2.3.0 tensorflow-hub
pip install google-cloud-storage==1.16.1
pip install google-cloud-logging==1.15.1
```
