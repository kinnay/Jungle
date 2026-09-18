
import setuptools

long_description = \
    "This library implements various file formats that are seen in Nintendo games."

setuptools.setup(
    name = "python-jungle",
    version = "0.0.3",
    description = "A library to work with Nintendo file formats.",
    long_description = long_description,
    author = "Yannik Marchand",
    author_email = "ymarchand@me.com",
    url = "https://github.com/kinnay/jungle",
    license = "GPLv3",
    packages = ["jungle"],
    package_data = {
        "jungle": ["files/*"]
    }
)
