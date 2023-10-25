from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='requestez',
    version='0.1.2',
    author='shashstormer',
    description='A simpler interface for scraping with some basic parsing, aes encryption decryption and some logging utils.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'requests', "m3u8", "pycryptodome", "yarl", "regex", "beautifulsoup4", "js2xml", "xmltodict"
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries',
        'Topic :: Internet :: WWW/HTTP',
    ],
    project_urls={
        'GitHub': 'https://github.com/shashstormer/requestez',
    },
)
