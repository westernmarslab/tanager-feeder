from setuptools import setup, find_packages
import platform
import io

def is_raspberrypi():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower(): return True
    except Exception:
        pass
    return False

opsys: str = platform.system()
if opsys == "Windows":
    install_requires = ["pywinauto", "pyautogui", "tanager_tcp", "numpy", "matplotlib","colorutils", "cython", "numpy", "playsound", "psutil", "pygame>=1.9.5,<1.9.7", "tanager-tcp"]
else:
    install_requires = ["colorutils", "cython", "matplotlib", "numpy", "playsound", "psutil", "pygame>=1.9.5,<1.9.7", "tanager-tcp"]

setup(
    name='tanager-feeder',
    version='1.8',
    packages=find_packages(),
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    description='Control software for spectroscopy using ASD RS3 and ViewSpec Pro',
    long_description=open('README.txt').read(),
    url='https://github.com/westernmarslab/tanager-feeder',
    author='Kathleen Hoza',
    author_email='kathleen@firstmode.com',
    entry_points={
        "console_scripts": [
            "tanager-feeder = tanager_feeder.__main__:main",
            "asd-feeder = asd_feeder.__main__:main",
            "pi-feeder = pi_feeder.pi_controller:main",
            "asd-watchdog = asd_feeder.asd_watchdog:main"
        ],
    },
    install_requires=install_requires,
    python_requires='>=3',
    include_package_data=True
)

