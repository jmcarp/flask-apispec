import re
from setuptools import setup
from setuptools import find_packages

REQUIRES = [
    'flask>=0.10.1',
    'marshmallow>=3.0.0',
    'webargs>=6.0.0',
    'apispec>=1.0.0,<4.0.0',
]


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ''
    with open(fname) as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError('Cannot find version information')
    return version


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name='flask-apispec',
    version=find_version('flask_apispec/__init__.py'),
    description='Build and document REST APIs with Flask and apispec',
    long_description=read('README.rst'),
    author='Joshua Carp',
    author_email='jm.carp@gmail.com',
    url='https://github.com/jmcarp/flask-apispec',
    packages=find_packages(exclude=('test*', )),
    package_dir={'flask_apispec': 'flask_apispec'},
    include_package_data=True,
    install_requires=REQUIRES,
    license='MIT',
    zip_safe=False,
    keywords='flask marshmallow webargs apispec',
    python_requires=">=3.5",
    test_suite='tests',
    project_urls={
        'Bug Reports': 'https://github.com/jmcarp/flask-apispec/issues',
        'Changelog': 'https://flask-apispec.readthedocs.io/en/latest/changelog.html',
    },
)
