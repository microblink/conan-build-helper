Add following code to the beginning of your `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.10)

if( NOT EXISTS "${CMAKE_BINARY_DIR}/mb_conan_build.cmake" )
    message( STATUS "Downloading mb_conan_build.cmake from https://github.com/microblink/conan-build-helper" )
    file( DOWNLOAD "https://raw.githubusercontent.com/microblink/conan-build-helper/master/mb_conan_build.cmake" "${CMAKE_BINARY_DIR}/mb_conan_build.cmake" )
endif()

include( ${CMAKE_BINARY_DIR}/mb_conan_build.cmake )
```

Also, ensure that you add `"CMakeBuild/[>=1.1.2,<2.0.0]@microblink/master"` entry to your `conanfile.py`.