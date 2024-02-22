# nmos-cpp Example Applications

This project demonstrates how to use the [nmos-cpp](https://github.com/sony/nmos-cpp) library as a dependency.

At the moment, these instructions are terse and the project contains a single example application, `my-nmos-node`, with code taken directly from `nmos-cpp-node` in the nmos-cpp repo.

Contributions are welcome.

## Preparation

### Compiler

* Visual Studio 2015 or higher (Visual Studio 2019 is tested on Windows 10)
* GCC 4.9 or higher (GCC 11 is tested on Ubuntu 22.04)
* Clang 4 or higher

### CMake

1. Download and install a recent [CMake stable release](https://cmake.org/download/#latest) for your platform  
   Notes:
   - Currently, CMake 3.17 or higher is required; version 3.24.3 (latest release at the time) has been tested
   - Pre-built binary distributions are available for many platforms
   - On Linux distributions, e.g. Ubuntu 14.04 LTS (long-term support), the pre-built binary version available via ``apt-get`` may be too out-of-date  
     Fetch, build and install a suitable version:  
     ```sh
     wget "https://cmake.org/files/v3.24/cmake-3.24.3.tar.gz"
     tar -zxvf cmake-3.24.3.tar.gz
     cd cmake-3.24.3
     ./bootstrap
     make
     sudo make install
     cd ..
     ```

### Conan

This project uses [Conan](https://conan.io) to download the rest of its dependencies.

1. Install Python 3 if necessary  
   Note: The Python scripts directory needs to be added to the `PATH`, so the Conan executable can be found
2. Install or upgrade Conan using `pip install --upgrade conan~=2.0.5`  
   Notes:
   - On some platforms with Python 2 and Python 3 both installed this may need to be `pip3 install --upgrade conan~=2.0.5`
   - Conan 2.0.5 or higher is required; dependencies may require a higher version; version 2.0.17 (latest release at the time) has been tested
   - Conan 1.X is no longer supported

## Build

**Windows**

For example, using the Visual Studio 2019 Developer Command Prompt:

```sh
mkdir build
cd build
conan install ../my-nmos-node -g CMakeToolchain --settings:all build_type=Debug --build=missing --output-folder=conan
conan install ../my-nmos-node -g CMakeToolchain --settings:all build_type=Release --build=missing --output-folder=conan
cmake .. ^
  -G "Visual Studio 16 2019" ^
  -DCMAKE_CONFIGURATION_TYPES:STRING="Debug;Release" ^
  -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake
```

Then, open and build the generated Visual Studio Solution, or use CMake's build tool mode:

```sh
cmake --build . --config <Debug-or-Release>
```

**Linux**

For example, using the default profile and dependencies:

```sh
mkdir build
cd build
conan install ../my-nmos-node -g CMakeToolchain --settings:all build_type=<Debug-or-Release> --build=missing --output-folder=conan
cmake .. \
  -DCMAKE_BUILD_TYPE:STRING="<Debug-or-Release>" \
  -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake
make
```

## Multi-nmos-cpp-node Launcher

The [nmos-multi-node](nmos-multi-node/) script enables scalability testing of NMOS systems with many Nodes.
