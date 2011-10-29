from setuptools import setup

setup(
    name='visutils',
    version='0.0.3',
    url="http://github.com/vis-netlausnir/visutils/",
    license="BSD",
    author="Netlausnir VIS",
    author_email="netlausnir@vis.is",
    description="Various Handy Utilities",
    packages=['visutils','visutils.data','visutils.django','visutils.isl'],
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
