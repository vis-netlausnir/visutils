from setuptools import setup

setup(
    name='visutils',
    version='0.0.2',
    url="http://github.com/vis-netlausnir/visutils/",
    license="BSD",
    author="Netlausnir VIS",
    author_email="netlausnir@vis.is",
    description="Various Handy Utilities",
    packages=['visutils'],
    zip_safe=False,
    platforms='any',
    dependency_links = [
    i,
    install_requires=[
        #'distribute>=0.6.19',
    ],
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
