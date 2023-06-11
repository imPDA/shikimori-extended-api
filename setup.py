from setuptools import setup

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

packages = [
    'shikimori_extended_api',
    'shikimori_extended_api.datatypes'
]

setup(
    name='shikimori-extended-api',
    version='v0.1.dev1',

    url='https://github.com/imPDA/shikimori-extended-api',
    author='imPDA',
    author_email='impda@mail.ru',
    package_dir={'': 'src'},
    packages=packages,
    install_requires=requirements,
)
