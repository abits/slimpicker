from setuptools import setup, find_packages

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
        'requests >= 1.1'
    ],
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        'console_scripts' : [
            'slimpicker = slimpicker.ui.main_func'
        ]
    }
)