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

To use `MicroblinkConanFile`, add this to your conan recipe in `conanfile.py`:

```python
from conans import ConanFile

class MyConanRecipe(ConanFile):
    # name, license, description, etc.
    # ( ... )
    python_requires = 'MicroblinkConanFile/<latest-version>@microblink/stable'
    python_requires_extend = 'MicroblinkConanFile.MicroblinkConanFile' # or MicroblinkConanFile.MicroblinkRecognizerConanFile
    # the rest of your recipe
    # ( ... )

    # if you have custom settings, options or default options that need to be merged with base,
    # you need to implement init() method to do the merging. For example
    def init(self):
        base = self.python_requires['MicroblinkConanFile'].module.MicroblinkConanFile
        self.options.update(base.options)
        self.default_options.update(base.default_options)
```

You can search for latest available version of `MicroblinkConanFile` with `conan search -r all MicroblinkConanFile`

**NOTE**: This syntax of `python_requires` requires Conan v1.24.0 or newer. If you need to use older version of Conan, please use MicroblinkConanFile v5.x or older.

For more information about the `python_requires`, check [the official documentation](https://docs.conan.io/en/latest/extending/python_requires.html).
