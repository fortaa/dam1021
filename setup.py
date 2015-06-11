from distutils.core import setup

setup(
    name="dam1021",
    version="0.2",
    url="https://github.com/fortaa/dam1021",
    download_url = 'https://github.com/fortaa/dam1021/tarball/0.2',
    author="Forta(a)",
    author_email="fortaa@users.noreply.github.com",
    description="Python dam1021 interface",
    install_requires=['pyserial','xmodem'],
    py_modules=["dam1021"],
    package_dir={'': 'src'},
)
