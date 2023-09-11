from setuptools import setup, find_packages

PYTHON_VERSION_REQ = ">3.10.0"
IBLPYBPOD_CURRENT_VERSION = "3.0.2"

long_description = """
iblpybpod is a GUI application that enables interaction with the Bpod device from [Sanworks](https://sanworks.io/). Much credit 
and thanks go to the original creators of the [pybpod project](https://github.com/pybpod/pybpod).
"""

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
