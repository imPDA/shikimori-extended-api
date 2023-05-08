from setuptools import setup

requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

packages = [
    'api',
]

setup(
    name='shikimori-extended-api',
    version='dev',

    url='https://github.com/imPDA/shikimori-extended-api',
    author='imPDA',
    author_email='impda@mail.ru',
    package_dir={'': 'src'},
    packages=packages,
    install_requires=requirements,
)
