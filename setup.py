from setuptools import find_packages
from setuptools import setup

setup (
    name='citk_version_updater',
    version='0.2',

    # Fill in these to make your Egg ready for upload to
    # PyPI
    author='DivineThreepwood',
    author_email='divine@openbase.org',

    description='A small tool to detect release versions of a citk project via scm and to '
           'update those versions in the project recipe. '
           'Additionally a specific version can be set within a defined distribution file as well.',
    url='https://github.com/csra/citk-version-updater',
    license="LGPLv3",
    long_description='Upgrade tool for citk projects. Project tags are synchronized with the remote repository and the latest release can be configured for a given distribution.',

    packages=find_packages('src'),
    package_dir={'': 'src'},
    zip_safe=True,

    # Declare your packages' dependencies here, for eg:
    install_requires=['GitPython', 'termcolor'],

    entry_points={
        "console_scripts": [
            "citk-version-updater = citk_version_updater.main:entry_point",
        ]
    },
)
