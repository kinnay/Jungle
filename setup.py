
import setuptools

long_description = \
	"This library implements various file formats that are seen in Nintendo games."

setuptools.setup(
	name = "jungle",
	version = "0.0.1",
	description = "A library to work with Nintendo file formats.",
	long_description = long_description,
	author = "Yannik Marchand",
	author_email = "ymarchand@me.com",
	url = "https://github.com/kinnay/jungle",
	license = "MIT",
	packages = ["jungle"],
	package_data = {
		"jungle": ["files/*"]
	}
)
