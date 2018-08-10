Add following code to the beginning of your `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.10)

if( NOT EXISTS "${CMAKE_CURRENT_BINARY_DIR}/mb_conan_build.cmake" )
    message( STATUS "Downloading mb_conan_build.cmake from https://github.com/microblink/conan-build-helper" )
    file( DOWNLOAD "https://raw.githubusercontent.com/microblink/conan-build-helper/master/mb_conan_build.cmake" "${CMAKE_CURRENT_BINARY_DIR}/mb_conan_build.cmake" )
endif()

include( ${CMAKE_CURRENT_BINARY_DIR}/mb_conan_build.cmake )
```

Also, ensure that you add `"CMakeBuild/[>=1.0.0,<2.0.0]@microblink/stable"` entry to your `conanfile.py`.

To use `MicroblinkConanFile`, add this to the beginning of your `conanfile.py`:

```python
from conans import tools

tools.download('https://raw.githubusercontent.com/microblink/conan-build-helper/master/mb_conan_helpers.py', 'mb_conan_helpers.py', overwrite=True)

from mb_conan_helpers import MicroblinkConanFile
```