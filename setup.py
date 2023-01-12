from setuptools import setup, find_packages

PYTHON_VERSION_REQ = ">3.8.0"
IBLPYBPOD_CURRENT_VERSION = "2.0.1"

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    require = [x.strip() for x in f.readlines() if not x.startswith('git+')]

setup(
    name="iblpybpod",
    version=IBLPYBPOD_CURRENT_VERSION,
    python_requires=PYTHON_VERSION_REQ,
    description="IBL implementation of pybpod software",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="IBL Staff",
    url="https://github.com/int-brain-lab/iblpybpod/",
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=['scratch', 'tests']),  # same as name
    include_package_data=True,
    install_requires=require,
    entry_points={"console_scripts": ["start-pybpod=pybpodgui_plugin.__main__:start"]},
    scripts=[]
)
