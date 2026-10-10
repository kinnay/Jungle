
import setuptools

long_description = \
    "This library implements various file formats that are seen in Nintendo " \
    "games."

packages = setuptools.find_namespace_packages(
    include = ["jungle", "jungle.*"],
    exclude = ["jungle.files"]
)

setuptools.setup(
    name = "python-jungle",
    version = "0.0.5",
    description = "A library to work with Nintendo file formats.",
    long_description = long_description,
    author = "Yannik Marchand",
    author_email = "ymarchand@me.com",
    url = "https://github.com/kinnay/jungle",
    license = "GPLv3",
    packages = packages,
    package_data = {
        "jungle": ["files/*"]
    }
)
