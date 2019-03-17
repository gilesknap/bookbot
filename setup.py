import io

from setuptools import find_packages, setup

with io.open('README.rst', 'rt', encoding='utf8') as f:
    readme = f.read()

setup(
    name='bookbot',
    version='0.0.1',
    url='https://github.com/gilesknap/bookbot/',
    license='Apache 2.0',
    maintainer='Giles Knap',
    maintainer_email='gilesknap@gmail.com',
    description='The basic booking app for Caversham fitness',
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
    ],
    extras_require={
        'test': [
            'pytest',
            'coverage',
        ],
    },
)
