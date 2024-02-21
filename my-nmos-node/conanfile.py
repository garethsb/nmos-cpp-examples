from conan import ConanFile


class MyNmosNodeRecipe(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps"

    def requirements(self):
        self.requires("nmos-cpp/cci.20221203")
        self.requires("json-schema-validator/2.3.0", override=True)
        self.requires("nlohmann_json/3.11.3", override=True)
