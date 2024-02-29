from setuptools import setup

package_name = 'wall-e'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fritis',
    maintainer_email='ifritis2020@udec.cl, jfritis2020@udec.cl',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
          'wal_publisher = wall-e.wal_pub:main',
          'wal_subscriber = wall-e.wal_sub:main',
        ],
    },
)
