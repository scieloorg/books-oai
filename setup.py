import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid >= 1.5',
    'pyramid_debugtoolbar >= 2.0.2',
    'waitress >= 0.8.8',
    'pymongo >= 2.7',
    'requests >= 2.2.1',
    'mock >= 1.0.1',
    'picles.plumber >= 0.11',
    'lxml >= 3.3.5',
    'simpleslug >= 1.0'
    ]

setup(name='booksoai',
      version='0.0',
      description='booksoai',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Programming Language :: Python :: 2.7",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="booksoai.tests",
      entry_points="""\
      [paste.app_factory]
      main = booksoai:main
      """,
      )
