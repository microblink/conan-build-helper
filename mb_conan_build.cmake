cmake_minimum_required(VERSION 3.10)

include_guard()

if( CONAN_EXPORTED ) # in conan local cache
    # standard conan installation, deps will be defined in conanfile.py
    # and not necessary to call conan again, conan is already running
    if( EXISTS ${CMAKE_BINARY_DIR}/conanbuildinfo_multi.cmake )
        include( ${CMAKE_BINARY_DIR}/conanbuildinfo_multi.cmake )
    else()
        include( ${CMAKE_BINARY_DIR}/conanbuildinfo.cmake )
    endif()
    set( basic_setup_params TARGETS )
    if( IOS )
        list( APPEND basic_setup_params NO_OUTPUT_DIRS )
    endif()
    conan_basic_setup( ${basic_setup_params} )
else() # in user space
    # Download automatically, you can also just copy the conan.cmake file
    if( NOT EXISTS "${CMAKE_BINARY_DIR}/conan.cmake" )
       message( STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan" )
       file( DOWNLOAD "https://raw.githubusercontent.com/conan-io/cmake-conan/v0.12/conan.cmake" "${CMAKE_BINARY_DIR}/conan.cmake" SHOW_PROGRESS )
    endif()
    include( ${CMAKE_BINARY_DIR}/conan.cmake )

    set( conan_cmake_run_params BASIC_SETUP CMAKE_TARGETS )
    if( IOS )
        list( APPEND conan_cmake_run_params NO_OUTPUT_DIRS )
    endif()
    # install development version of packages if MB_DEV_RELEASE or building in debug mode
    if( MB_DEV_RELEASE OR "${CMAKE_BUILD_TYPE}" STREQUAL "Debug" )
        list( APPEND conan_cmake_run_params BUILD_TYPE "Debug" )
    endif()

    # detect profile
    if( IOS )
        list( APPEND conan_cmake_run_params PROFILE ios )
    elseif( ANDROID )
        list( APPEND conan_cmake_run_params PROFILE android-${ANDROID_ABI} )
    endif()

    # other cases should be auto-detected by conan.cmake

    # Make sure to use conanfile.py to define dependencies, to stay consistent
    conan_cmake_run( CONANFILE conanfile.py ${basic_setup_params} )
endif()