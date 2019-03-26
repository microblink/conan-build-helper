cmake_minimum_required(VERSION 3.10)

# in order to be able to detect AppleClang, as opposed to Clang, we need to set this policy
cmake_policy( SET CMP0025 NEW )

enable_language( C CXX  )

set( TESTING_DEFAULT OFF )

if( NOT CONAN_EXPORTED )
    set( TESTING_DEFAULT ON )
endif()

option( MB_ENABLE_TESTING "Enable testing" ${TESTING_DEFAULT} )

if( NOT CONAN_EXPORTED )
    if ( MB_ENABLE_TESTING )
        list( APPEND MB_CONAN_SETUP_PARAMS OPTIONS "enable_testing=True" )
    endif()
endif()

option( MB_SKIP_CONAN_INSTALL "Prevent CMake from calling conan install" OFF )
option( MB_BUILD_MISSING_CONAN_PACKAGES "Build conan packages that have not prebuilt binaries on the server available" ON)

# in conan local cache or user has already performed conan install command
if( CONAN_EXPORTED OR MB_SKIP_CONAN_INSTALL )
    # standard conan installation, deps will be defined in conanfile.py
    # and not necessary to call conan again, conan is already running
    if( EXISTS ${CMAKE_CURRENT_BINARY_DIR}/conanbuildinfo_multi.cmake )
        include( ${CMAKE_CURRENT_BINARY_DIR}/conanbuildinfo_multi.cmake )
    else()
        include( ${CMAKE_CURRENT_BINARY_DIR}/conanbuildinfo.cmake )
    endif()
    set( basic_setup_params TARGETS )
    if( IOS )
        list( APPEND basic_setup_params NO_OUTPUT_DIRS )
    endif()
    conan_basic_setup( ${basic_setup_params} )
else() # in user space and user has not performed conan install command

    if( MB_JENKINS_BUILD AND ANDROID AND NOT MB_NO_LOG_DEPENDENCY )
        list( APPEND MB_CONAN_SETUP_PARAMS OPTIONS "LogAndTimer:redirect_to_stdout=True" )
    endif()

    if( CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE )
        set( CONAN_CMAKE_MULTI ON )
    else()
        set( CONAN_CMAKE_MULTI OFF )
    endif()

    # if not using IDE generator and build type is not set, use Release build type
    if ( NOT CONAN_CMAKE_MULTI AND NOT CMAKE_BUILD_TYPE )
        set( CMAKE_BUILD_TYPE Release )
    endif()

    # Download automatically, you can also just copy the conan.cmake file
    if( NOT EXISTS "${CMAKE_BINARY_DIR}/conan.cmake" )
       message( STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan" )
       file( DOWNLOAD "https://raw.githubusercontent.com/conan-io/cmake-conan/v0.13/conan.cmake" "${CMAKE_BINARY_DIR}/conan.cmake" )
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

    if ( MB_DEV_RELEASE AND CMAKE_GENERATOR MATCHES "Visual Studio" AND NOT CMAKE_BUILD_TYPE )
        set( CMAKE_BUILD_TYPE Debug ) # required to correctly detect VS runtime toolset
    endif()

    # detect profile
    set( HAVE_PROFILE OFF )
    if( IOS )
        list( APPEND conan_cmake_run_params PROFILE ios )
        set( HAVE_PROFILE ON )
    elseif( ANDROID )
        list( APPEND conan_cmake_run_params PROFILE android-${ANDROID_ABI} )
        set( HAVE_PROFILE ON )
    elseif( CMAKE_SYSTEM_NAME STREQUAL "Linux" )
        if( "${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang" )
            list( APPEND conan_cmake_run_params PROFILE clang )
        else()
            list( APPEND conan_cmake_run_params PROFILE gcc )
        endif()
        set( HAVE_PROFILE ON )
    elseif( CMAKE_SYSTEM_NAME STREQUAL "Darwin" )
        list( APPEND conan_cmake_run_params PROFILE macos )
    endif()

    if( MB_CONAN_SETUP_PARAMS )
        list( APPEND conan_cmake_run_params ${MB_CONAN_SETUP_PARAMS} )
    endif()

    if ( HAVE_PROFILE )
        # use automatically detected build type when using profile
        list( APPEND conan_cmake_run_params PROFILE_AUTO build_type )
    endif()

    # other cases should be auto-detected by conan.cmake

    # Make sure to use conanfile.py to define dependencies, to stay consistent
    if ( CONANFILE_LOCATION )
        set( CONANFILE ${CONANFILE_LOCATION} )
    else()
        if ( EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/conanfile.py )
            set( CONANFILE conanfile.py )
        elseif( EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/conanfile.txt )
            set( CONANFILE conanfile.txt )
        endif()
    endif()
    if ( NOT CONANFILE )
        message( FATAL_ERROR "Cannot find neither conanfile.py nor conanfile.txt in current source directory. You can also use CONANFILE_LOCATION to specify path to either conanfile.py or conanfile.txt and override automatic detection." )
    endif()

    if ( MB_BUILD_MISSING_CONAN_PACKAGES )
        list( APPEND conan_cmake_run_params BUILD missing )
    endif()

    conan_cmake_run( CONANFILE ${CONANFILE} ${conan_cmake_run_params} )

    if ( CONAN_CMAKE_MULTI )
        # workaround for https://github.com/conan-io/conan/issues/1498
        # in our case, it's irrelevant which version is added - we need access to cmake files
        set(CMAKE_PREFIX_PATH ${CONAN_CMAKE_MODULE_PATH_RELEASE} ${CMAKE_PREFIX_PATH})
        set(CMAKE_MODULE_PATH ${CONAN_CMAKE_MODULE_PATH_RELEASE} ${CMAKE_MODULE_PATH})
    endif()
endif()

# if this include fails, then you have forgot to add
# build_requires = "CMakeBuild/<latest-version>@microblink/stable"
# to your conanfile.py
include( common_settings )