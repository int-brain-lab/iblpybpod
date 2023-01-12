# iblpybpod #

**version:** 2

iblpybpod is a GUI application that enables interaction with the Bpod device from [Sanworks](https://sanworks.io/). Much credit 
and thanks go to the original creators of the [pybpod project](https://github.com/pybpod/pybpod).

This project has recently been adopted by the software development team at the International Brain Lab to bring the code into 
modernity.

## Installation for use

Currently, only Python v3.8 on Ubuntu 22.04 and Windows 10 is being tested.

### Python venv commands for setup
```bash
python3.8 -m venv iblpybpod
source iblpybpod/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install iblpybpod
start-pybpod
```

---

## For developers
This repository is adhering to the following conventions:
* [semantic versioning](https://semver.org/) for consistent version numbering logic
* [gitflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) for managing branches 
* [Flake8](https://flake8.pycqa.org/) for style guide enforcement 

![](README_semver.png)
![](README_gitflow_workflow.png)

Please review these conventions to more easily contribute to the project.

### New feature branches:
- a `new_feature` branch is forked from the current `develop` branch
- the `new_feature` branch is then merged back into the `develop` branch
- the `new_feature` branch will eventually be deleted

### Release candidate branches:
- a release candidate, `rc` branch is a "pre-release" branch for beta testers on production rigs
- the `rc` branch is forked from the `develop` branch
- once the `rc` has been thoroughly tested, it will be merged into `master` and `develop`
- the `rc` branch will eventually be deleted

### Hotfix branches:
- a `hotfix` or `maintenance` branch is forked from `master`
- once the fix has been thoroughly tested, it will get merged back into `master` and `develop`
- the `hotfix` branch will eventually be deleted

### Python venv commands for setup
```bash
python3.8 -m venv iblpybpod-dev
source iblpybpod-dev/bin/activate
python -m pip install --upgrade pip wheel
git clone https://github.com/int-brain-lab/iblpybpod
python -m pip install --editable iblpybpod
```
