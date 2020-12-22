from setuptools import setup

setup(
    name='tanager-feeder',
    version='0.0.6',
    packages=['tanager_feeder'],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    description='Control software for spectroscopy using ASD RS3 and ViewSpec Pro',
    long_description=open('README.txt').read(),
    url='https://github.com/kathleenhoza/autospectroscopy',
    author='Kathleen Hoza',
    author_email='kathleenhoza@gmail.com',
    project_urls={
        'Source':'https://github.com/kathleenhoza/autospectroscopy'
    },
    entry_points={
        "console_scripts": [
            "tanager-feeder = tanager_feeder.__main__:main",
        ],
    },
    install_requires=["colorutils", "cython", "matplotlib", "numpy", "playsound", "pygame", "tanager-tcp"],
    python_requires='>=3',
    include_package_data=True
)
