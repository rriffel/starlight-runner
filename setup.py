from setuptools import setup, find_packages

setup(
    name="starlight-runner",
    version="1.0.0",
    description="A modern GUI and workflow tool for preparing spectra, creating masks, running STARLIGHT stellar population synthesis, and analyzing results.",
    author="Rogério Riffel",
    author_email="riffel@ufrgs.br",
    url="https://github.com/rriffel/starlight-runner",
    packages=find_packages(include=["starlight_runner", "starlight_runner.*"]),
    package_data={"starlight_runner": ["templates/*", "assets/*"]},
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
        "PyQt5>=5.15.0",
        "astropy>=5.0.0",
    ],
    entry_points={
        "console_scripts": [
            "starlight-runner=starlight_runner.main_gui:main",
        ],
        "gui_scripts": [
            "starlight-runner-gui=starlight_runner.main_gui:main",
        ],
    },
)
