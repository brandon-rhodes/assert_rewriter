try:
    from setuptools import setup
except:
    from distutils.core import setup

setup(
    name='assert_rewriter',
    version='1.0',
    description='Rewrite function bytecode to support assert introspection.',
    long_description=open('README.rst').read(),
    license='MIT',
    author='Brandon Rhodes',
    author_email='brandon@rhodesmill.org',
    url='https://github.com/brandon-rhodes/assert_rewriter/',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    packages=['assert_rewriter'],
)
