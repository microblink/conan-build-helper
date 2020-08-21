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
option( MB_BUILD_MISSING_CONAN_PACKAGES "Build conan packages that have not prebuilt binaries on the server available" ON )

if( NOT COMMAND remote_include )
    macro( remote_include file_name url fallback_url )
        if( NOT EXISTS "${CMAKE_BINARY_DIR}/${file_name}" )
            set( download_succeeded FALSE )
            foreach( current_url ${url} ${fallback_url} )
                set( download_attempt 1 )
                set( sleep_seconds 1 )
                while( NOT ${download_succeeded} AND ${download_attempt} LESS_EQUAL 3 )
                    message( STATUS "Downloading mb_conan_build.cmake from ${current_url}. Attempt #${download_attempt}" )
                    file(
                        DOWNLOAD
                            "${current_url}"
                            "${CMAKE_BINARY_DIR}/${file_name}"
                        SHOW_PROGRESS
                        TIMEOUT
                            2  # 2 seconds timeout
                        STATUS
                            download_status
                    )
                    list( GET download_status 0 error_status      )
                    list( GET download_status 1 error_description )
                    if ( error_status EQUAL 0 )
                        set( download_succeeded TRUE )
                    else()
                        message( STATUS "Download failed due to error: [code: ${error_status}] ${error_description}" )
                        math( EXPR download_attempt "${download_attempt} + 1" OUTPUT_FORMAT DECIMAL )
                        math( EXPR sleep_seconds "${sleep_seconds} + 1" OUTPUT_FORMAT DECIMAL )
                        message( STATUS "Sleep ${sleep_seconds} seconds" )
                        execute_process( COMMAND "${CMAKE_COMMAND}" -E sleep "${sleep_seconds}" )
                    endif()
                endwhile()
                if ( ${download_succeeded} )
                    # break the foreach loop
                    break()
                else()
                    # remove empty file
                    file( REMOVE "${CMAKE_BINARY_DIR}/${file_name}" )
                endif()
            endforeach()
            if ( NOT ${download_succeeded} )
                # remove empty file
                file( REMOVE "${CMAKE_BINARY_DIR}/${file_name}" )
                message( FATAL_ERROR "Failed to download ${file_name}, even after ${download_attempt} retrials. Please check your Internet connection!" )
            endif()
        endif()

        include( ${CMAKE_BINARY_DIR}/${file_name} )
    endmacro()
endif()

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

    if( ANDROID_STUDIO_WRAPPED_EXE AND MB_AS_HAS_GTEST )
        list( APPEND MB_CONAN_SETUP_PARAMS OPTIONS "GTest:redirect_to_android_log=True" )
    endif()

    if ( DEFINED MB_ENABLE_LTO )
        if ( MB_ENABLE_LTO )
            list( APPEND MB_CONAN_SETUP_PARAMS SETTINGS "link_time_optimization=True" )
        else()
            list( APPEND MB_CONAN_SETUP_PARAMS SETTINGS "link_time_optimization=False" )
        endif()
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

    remote_include( "conan.cmake" "http://raw.githubusercontent.com/microblink/cmake-conan/v0.15.1/conan.cmake" "http://files.microblink.com/conan.cmake" )

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

    if ( MSVC AND NOT CMAKE_GENERATOR MATCHES "Visual Studio" )
        if ( "${CMAKE_BUILD_TYPE}" STREQUAL "Debug" OR MB_DEV_RELEASE )
            # set compiler runtime to MDd
            list( APPEND conan_cmake_run_params SETTINGS compiler.runtime=MDd )
        else()
            list( APPEND conan_cmake_run_params SETTINGS compiler.runtime=MD )
        endif()
    endif()

    # detect profile
    set( HAVE_PROFILE OFF )
    if( IOS )
        # iOS will use Apple Clang - determine version and decide which profile to use
        string( REPLACE "." ";" VERSION_LIST ${CMAKE_CXX_COMPILER_VERSION} )
        list( GET VERSION_LIST 0 apple_clang_major_version )
        list( GET VERSION_LIST 1 apple_clang_minor_version  )
        list( GET VERSION_LIST 2 apple_clang_bugfix_version )

        list( APPEND conan_cmake_run_params PROFILE ios-clang-${apple_clang_major_version}.${apple_clang_minor_version}.${apple_clang_bugfix_version} )
        set( HAVE_PROFILE ON )
    elseif( ANDROID )
        set( ndk_revision_suffix )
        if ( ANDROID_NDK_MINOR EQUAL 1 )
            set( ndk_revision_suffix b )
        elseif ( ANDROID_NDK_MINOR EQUAL 2 )
            set( ndk_revision_suffix c )
        endif()
        list( APPEND conan_cmake_run_params PROFILE android-ndk-r${ANDROID_NDK_MAJOR}${ndk_revision_suffix}-${ANDROID_ABI} )
        set( HAVE_PROFILE ON )
    elseif( MSVC )
        string( REPLACE "." ";" VERSION_LIST ${CMAKE_CXX_COMPILER_VERSION} )
        list( GET VERSION_LIST 0 compiler_major_version )
        list( GET VERSION_LIST 1 compiler_minor_version )

        # msvc-xx.yy profile will use Ninja generator (assumes vcvars are already set)
        # vc-xx.yy profile will use Visual Studio generator (no vcvars required - use always latest available msvc)

        set( msvc_profile_name "msvc" )
        if ( CMAKE_GENERATOR MATCHES "Visual Studio" )
            set( msvc_profile_name "vs" )
        endif()

        list( APPEND conan_cmake_run_params PROFILE ${msvc_profile_name}-${compiler_major_version}.${compiler_minor_version} )

        set( HAVE_PROFILE ON )
    elseif( CMAKE_SYSTEM_NAME STREQUAL "Linux" )
        string( REPLACE "." ";" VERSION_LIST ${CMAKE_CXX_COMPILER_VERSION} )
        list( GET VERSION_LIST 0 compiler_major_version )
        list( GET VERSION_LIST 1 compiler_minor_version )

        set( linux_optimization_suffix )
        if ( DEFINED MB_INTEL_OPTIMIZATION AND NOT MB_INTEL_OPTIMIZATION STREQUAL "generic" )
            set( linux_optimization_suffix "-${MB_INTEL_OPTIMIZATION}" )
        endif()

        if( "${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang" )
            list( APPEND conan_cmake_run_params PROFILE clang${compiler_major_version}-linux${linux_optimization_suffix} )
        else()
            list( APPEND conan_cmake_run_params PROFILE gcc-${compiler_major_version}.${compiler_minor_version}-linux${linux_optimization_suffix} )
            option( MB_USE_GCC_CXX11_ABI "Use modern CXX11 ABI for GCC builds" ON )
            if ( MB_USE_GCC_CXX11_ABI )
                list( APPEND conan_cmake_run_params SETTINGS compiler.libcxx=libstdc++11 )
            else()
                list( APPEND conan_cmake_run_params SETTINGS compiler.libcxx=libstdc++ )
            endif()
        endif()
        set( HAVE_PROFILE ON )
    elseif( CMAKE_SYSTEM_NAME STREQUAL "Darwin" )
        string( REPLACE "." ";" VERSION_LIST ${CMAKE_CXX_COMPILER_VERSION} )
        list( GET VERSION_LIST 0 apple_clang_major_version  )
        list( GET VERSION_LIST 1 apple_clang_minor_version  )
        list( GET VERSION_LIST 2 apple_clang_bugfix_version )

        list( APPEND conan_cmake_run_params PROFILE macos-clang-${apple_clang_major_version}.${apple_clang_minor_version}.${apple_clang_bugfix_version} )
        set( HAVE_PROFILE ON )
    elseif( EMSCRIPTEN )
        string( REPLACE "." ";" VERSION_LIST ${CMAKE_CXX_COMPILER_VERSION} )
        list( GET VERSION_LIST 0 clang_major_version  )
        set( emscripten_backend "upstream" )
        if ( ${clang_major_version} EQUAL 6 )
            set( emscripten_backend "fastcomp" )
        endif()
        list( APPEND conan_cmake_run_params PROFILE emscripten-${EMSCRIPTEN_VERSION}-${emscripten_backend} )
        set( HAVE_PROFILE ON )

        if ( DEFINED MB_EMSCRIPTEN_COMPILE_TO_WEBASSEMBLY )
            if ( MB_EMSCRIPTEN_COMPILE_TO_WEBASSEMBLY )
                list( APPEND conan_cmake_run_params SETTINGS arch=wasm )
            else()
                list( APPEND conan_cmake_run_params SETTINGS arch=asm.js )
            endif()
        endif()

        if ( DEFINED MB_EMSCRIPTEN_ENABLE_PTHREADS )
            if ( MB_EMSCRIPTEN_ENABLE_PTHREADS )
                list( APPEND conan_cmake_run_params SETTINGS os.threads=true )
            else()
                list( APPEND conan_cmake_run_params SETTINGS os.threads=false )
            endif()
        endif()

        if ( DEFINED MB_EMSCRIPTEN_USE_WEBGL2 )
            if ( MB_EMSCRIPTEN_USE_WEBGL2 )
                list( APPEND conan_cmake_run_params SETTINGS os.webGLVersion=2 )
            else()
                list( APPEND conan_cmake_run_params SETTINGS os.webGLVersion=1 )
            endif()
        endif()

        if ( DEFINED MB_EMSCRIPTEN_TARGET_ENVIRONMENT )
            list( APPEND conan_cmake_run_params SETTINGS os.environment=${MB_EMSCRIPTEN_TARGET_ENVIRONMENT} )
        endif()

        if ( DEFINED MB_EMSCRIPTEN_SIMD )
            if ( MB_EMSCRIPTEN_SIMD )
                list( APPEND conan_cmake_run_params SETTINGS os.simd=true )
            else()
                list( APPEND conan_cmake_run_params SETTINGS os.simd=false )
            endif()
        endif()
    endif()

    if( MB_CONAN_SETUP_PARAMS )
        list( APPEND conan_cmake_run_params ${MB_CONAN_SETUP_PARAMS} )
    endif()

    if ( HAVE_PROFILE )
        # use automatically detected build type and runtime when using profile
        list( APPEND conan_cmake_run_params PROFILE_AUTO build_type compiler.runtime )
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
