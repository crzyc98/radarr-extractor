from setuptools import setup, find_packages

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name='radarr_extractor',
    version='0.1.0',
    packages=find_packages(),
    install_requires=install_requires,
    description='A tool to automatically extract downloaded movie files from Radarr and notify Radarr to rescan the extracted content.',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/radarr-extractor',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
