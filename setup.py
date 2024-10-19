from setuptools import setup, find_packages

setup(
    name='pytest-manufacturing-api',
    version='0.1.0',
    author='Mark Mayhew',
    author_email='mark.mayhew@javs.com',
    description='A pytest plugin to connect to manufacturing database api.',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pytest',
        'requests',
    ],
    entry_points={
        'pytest11': [
            'manufacturing_api = pytest_manufacturing_api.plugin',
        ],
    },
    classifiers=[
        'Framework :: Pytest',
    ],
    url='https://github.com/justiceavsolutions/pytest-manufacturing-api',
)