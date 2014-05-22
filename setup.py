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
    version="0.0",
    packages=find_packages(),

    author="Matthias Geier",
    author_email="Matthias.Geier@gmail.com",
    description="Schunk Motion Protocol for Python 3",
    license="MIT",
    keywords="Schunk RS232 servo motor".split(),
    url="http://github.com/spatialaudio/schunk",

    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)
