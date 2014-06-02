import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = '--doctest-modules --ignore setup.py'
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name="SchunkMotionProtocol",
    version="0.1.1",
    py_modules=['schunk'],

    author="Matthias Geier",
    author_email="Matthias.Geier@gmail.com",
    description="Schunk Motion Protocol for Python 3",
    long_description=open('README.rst').read(),
    license="MIT",
    keywords="Schunk RS232 servo motor".split(),
    url="http://schunk.rtfd.org/",
    download_url="https://github.com/spatialaudio/schunk/releases/",
    platforms='any',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
    ],

    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)
