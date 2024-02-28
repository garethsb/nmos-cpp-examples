from conan import ConanFile


class MyNmosNodeRecipe(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps"

    def requirements(self):
        self.requires("nmos-cpp/cci.20240223")
