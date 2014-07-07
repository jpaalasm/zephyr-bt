from setuptools import setup

setup(name='zephyr-bt',
      version='0.1',
      description='zephyr-bt is a Python library for interfacing with a Zephyr BioHarness(TM) device over a serial Bluetooth connection.',
      url='https://github.com/jpaalasm/zephyr-bt',
      author='Joonas Paalasmaa, David Murphy, Ove Holmqvist',
      author_email='joonas.paalasmaa@gmail.com',
      license='BSD',
      package_dir={'zephyr': 'src/zephyr'},
      packages=['zephyr'],
      zip_safe=True)
