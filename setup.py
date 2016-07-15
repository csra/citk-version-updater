from setuptools import setup, find_packages

setup (
       name = 'CitkProjectUpdater',
       version = '0.1',
       packages = find_packages(),

       # Fill in these to make your Egg ready for upload to
       # PyPI
       author = 'DivineThreepwood',
       author_email = 'divine@openbase.org',

       #summary = 'Just another Python package for the cheese shop',
       url = 'http://www.openbase.org',
       license = '',
       long_description = 'Upgrade tool for citk projects. Project tags are synchronized with the remote repository and the latest release can be configured for a given distribution.',

       # could also include long_description, download_url, classifiers, etc.
       
       # Declare your packages' dependencies here, for eg:
       install_requires = ['gitpython'],
)