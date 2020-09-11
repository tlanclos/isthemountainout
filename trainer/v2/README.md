# Is The Mountain Out? Trainer

## Getting Started

### Install Anaconda

Follow instructions at https://www.anaconda.com/products/individual/get-started

### Install Packages

Create a virtual environment named `tf_gpu` containing tensorflow including all cuda and cuDNN compatible versions.

```
conda create --name tf_gpu \
  tensorflow-gpu==2.1.0 \
  tensorflow-hub \
  ipykernel \
  ipython_genutils \
  nbformat \
  pillow \
  matplotlib
```
