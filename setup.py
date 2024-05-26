from setuptools import setup, find_packages

setup(
    name='ZeroXRequests',
    version='0.2.0',  # Atualize a versão
    description='A description of your package',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/rafax00/ZeroXRequests',
    author='rafax00',
    author_email='your.email@example.com',
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'requests',
        'h2',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
