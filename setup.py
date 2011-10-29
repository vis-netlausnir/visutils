import os
from setuptools import setup, find_packages

setup(
    name='visutils',
    version='0.0.4',
    url="http://github.com/vis-netlausnir/visutils/",
    license="BSD",
    author="Netlausnir VIS",
    author_email="netlausnir@vis.is",
    description="Various Handy Utilities",
    packages=find_packages(),
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
