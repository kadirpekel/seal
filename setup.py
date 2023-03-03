from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
cwd = Path(__file__).parent
long_description = (cwd / 'README.md').read_text()

setup(
    name='seal-lang',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['seal'],
    version='0.0.1',
    python_requires='>=3.7',
    description='Write meaningful teal in s-expressions!',
    author='Kadir Pekel',
    author_email='kadirpekel@gmail.com',
    packages=find_packages(include=['seal']),
    package_data={
        'seal': ['langspec.json']
    },
    url='https://github.com/kadirpekel/seal',
    install_requires=[
        'komandr>=2.0.1',
    ],
    extras_require={
        'dev': [
            'pytest',
            'flake8'    
        ]
    },
    tests_require=[
        'pytest'
    ],
    entry_points={
        'console_scripts': [
            'seal=seal.cli:main',
        ],
    },
)