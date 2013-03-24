from setuptools import setup

setup(
    name='slimpicker',
    version='0.1',
    url='https://bitbucket.org/cmartel/slimpicker',
    license='LICENSE.txt',
    author='Chris Martel',
    keywords='tv shows guide web',
    author_email='chris@codeways.org',
    description='Gather stuff from the interwebs.',
    long_description=open('README.txt').read(),
    install_requires=[
        'beautifulsoup4 >= 4.1.3',
        'distribute',
        'requests >= 1.1',
        'lxml >= 3.1.0',
        'chardet >= 2.0.0'
    ],
    packages=['slimpicker'],
    zip_safe=False,
    entry_points={
        'console_scripts' : [
            'slimpicker = slimpicker.ui:main_func'
        ]
    }
)
