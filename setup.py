import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'waitress',
    'pymongo',
    'requests',
    'mock',
    'plumber',
    'lxml'
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
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      dependency_links = ['http://github.com/gustavofonseca/plumber/tarball/master#egg=plumber'],
      install_requires=requires,
      tests_require=requires,
      test_suite="booksoai.tests",
      entry_points="""\
      [paste.app_factory]
      main = booksoai:main
      """,
      )
