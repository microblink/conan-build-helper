Add following code to the beginning of your `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.10)

if( NOT EXISTS "${CMAKE_BINARY_DIR}/mb_conan_build.cmake" )
    message( STATUS "Downloading mb_conan_build.cmake from https://github.com/microblink/conan-build-helper" )
    file( DOWNLOAD "https://raw.githubusercontent.com/microblink/conan-build-helper/master/mb_conan_build.cmake" "${CMAKE_BINARY_DIR}/mb_conan_build.cmake" )
endif()

include( ${CMAKE_BINARY_DIR}/mb_conan_build.cmake )
```

Also, ensure that you add `"CMakeBuild/<latest-version>@microblink/stable"` entry to your `conanfile.py`.

To use `MicroblinkConanFile`, add this to the beginning of your `conanfile.py`:

```python
from conans import tools, CMake, python_requires

base = python_requires('MicroblinkConanFile/<latest-version>@microblink/stable')
```

You can search for latest available version of `MicroblinkConanFile` with `conan search -r all MicroblinkConanFile`

**NOTE**: `python_requires` requires Conan v1.7.0 or newer.