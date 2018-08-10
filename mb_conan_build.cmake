cmake_minimum_required(VERSION 3.10)

# in order to be able to detect AppleClang, as opposed to Clang, we need to set this policy
cmake_policy( SET CMP0025 NEW )

enable_language( C CXX  )

# in conan local cache or user has already performed conan install command
if( CONAN_EXPORTED OR EXISTS ${CMAKE_CURRENT_BINARY_DIR}/conanbuildinfo_multi.cmake OR EXISTS ${CMAKE_CURRENT_BINARY_DIR}/conanbuildinfo.cmake )
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
    if( NOT EXISTS "${CMAKE_CURRENT_BINARY_DIR}/conan.cmake" )
       message( STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan" )
       file( DOWNLOAD "https://raw.githubusercontent.com/conan-io/cmake-conan/v0.12/conan.cmake" "${CMAKE_CURRENT_BINARY_DIR}/conan.cmake" )
    endif()
    include( ${CMAKE_CURRENT_BINARY_DIR}/conan.cmake )

    set( conan_cmake_run_params BASIC_SETUP CMAKE_TARGETS )
    if( IOS )
        list( APPEND conan_cmake_run_params NO_OUTPUT_DIRS )
    endif()
    # install development version of packages if MB_DEV_RELEASE or building in debug mode
    if( MB_DEV_RELEASE OR "${CMAKE_BUILD_TYPE}" STREQUAL "Debug" )
        list( APPEND conan_cmake_run_params BUILD_TYPE "Debug" )
    endif()

    # workaround for https://github.com/conan-io/cmake-conan/issues/85
    macro( mb_conan_cmake_run )
        parse_arguments( ${ARGV} )
        if( ARGUMENTS_PROFILE )
            # workaround (only for our specific use cases)
            set(settings -pr ${ARGUMENTS_PROFILE})
            conan_cmake_setup_conanfile(${ARGV})
            set(CONAN_OPTIONS "")
            if(ARGUMENTS_CONANFILE)
                set(CONANFILE ${CMAKE_CURRENT_SOURCE_DIR}/${ARGUMENTS_CONANFILE})
                # A conan file has been specified - apply specified options as well if provided
                foreach(ARG ${ARGUMENTS_OPTIONS})
                    set(CONAN_OPTIONS ${CONAN_OPTIONS} -o ${ARG})
                endforeach()
            else()
                set(CONANFILE ".")
            endif()

            set(CONAN_INSTALL_FOLDER "")
            if(ARGUMENTS_INSTALL_FOLDER)
                set(CONAN_INSTALL_FOLDER -if ${ARGUMENTS_INSTALL_FOLDER})
            endif()

            # if dev-release, then use cmake generator, not cmake_multi
            message( STATUS "CONAN_CMAKE_MULTI: ${CONAN_CMAKE_MULTI}, MB_DEV_RELEASE: ${MB_DEV_RELEASE}")
            if(CONAN_CMAKE_MULTI AND NOT MB_DEV_RELEASE)
                foreach(build_type "Release" "Debug")
                    set( CONAN_INVOCATION conan install ${CONANFILE} ${settings} -g cmake_multi ${CONAN_OPTIONS} -s build_type=${build_type} --build=missing )
                    string (REPLACE ";" " " _CONAN_INVOCATION "${CONAN_INVOCATION}")
                    message( STATUS "Conan executing: ${_CONAN_INVOCATION}" )
                    execute_process(
                        COMMAND
                            ${CONAN_INVOCATION}
                        RESULT_VARIABLE
                            return_code
                        WORKING_DIRECTORY
                            ${CMAKE_CURRENT_BINARY_DIR}
                    )
                    if( NOT "${return_code}" STREQUAL "0" )
                        message(FATAL_ERROR "Conan install failed='${return_code}'")
                    endif()
                endforeach()
            else()
                set( invocation_build_type ${CMAKE_BUILD_TYPE} )
                if( MB_DEV_RELEASE )
                    set( invocation_build_type "Debug" )
                endif()
                set( CONAN_INVOCATION conan install ${CONANFILE} ${settings} -g cmake ${CONAN_OPTIONS} -s build_type=${invocation_build_type} --build=missing )
                string (REPLACE ";" " " _CONAN_INVOCATION "${CONAN_INVOCATION}")
                message( STATUS "Conan executing: ${_CONAN_INVOCATION}" )
                execute_process(
                    COMMAND
                        ${CONAN_INVOCATION}
                    RESULT_VARIABLE
                        return_code
                    WORKING_DIRECTORY
                        ${CMAKE_CURRENT_BINARY_DIR}
                )
                if( NOT "${return_code}" STREQUAL "0" )
                    message(FATAL_ERROR "Conan install failed='${return_code}'")
                endif()
            endif()

            # if dev-release, trick conan_load_buildinfo into thinking that we do not have cmake_multi generator so
            # it will load correct cmakebuildinfo.cmake
            if( MB_DEV_RELEASE )
                set( CONAN_CMAKE_MULTI OFF )
            endif()
            conan_load_buildinfo()

            if(ARGUMENTS_BASIC_SETUP)
                foreach(_option CMAKE_TARGETS KEEP_RPATHS NO_OUTPUT_DIRS)
                    if(ARGUMENTS_${_option})
                        if(${_option} STREQUAL "CMAKE_TARGETS")
                            list(APPEND _setup_options "TARGETS")
                        else()
                            list(APPEND _setup_options ${_option})
                        endif()
                    endif()
                endforeach()
                conan_basic_setup(${_setup_options})
            endif()
        else()
            if( CONAN_CMAKE_MULTI AND ARGUMENTS_BUILD_TYPE )
                # if ARGUMENTS_BUILD_TYPE is set, we want given build type for all configurations, so we must
                # trick conan_cmake_run into thinking that cmake is not run under multi-config generator
                set( BACKUP_CMAKE_CONFIGURATION_TYPES ${CMAKE_CONFIGURATION_TYPES} )
                set( CMAKE_CONFIGURATION_TYPES "" )
                set( CMAKE_BUILD_TYPE ${ARGUMENTS_BUILD_TYPE} )
            endif()

            # call default implementation
            conan_cmake_run( ${ARGV} )

            # restore cmake configuration types from backup (if any)
            if( BACKUP_CMAKE_CONFIGURATION_TYPES )
                set( CMAKE_CONFIGURATION_TYPES ${BACKUP_CMAKE_CONFIGURATION_TYPES} )
                set( CMAKE_BUILD_TYPE "" )
            endif()
        endif()
    endmacro()

    # detect profile
    if( IOS )
        list( APPEND conan_cmake_run_params PROFILE ios )
    elseif( ANDROID )
        list( APPEND conan_cmake_run_params PROFILE android-${ANDROID_ABI} )
    elseif( CMAKE_SYSTEM_NAME STREQUAL "Linux" )
        if( "${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang" )
            list( APPEND conan_cmake_run_params PROFILE clang )
        else()
            list( APPEND conan_cmake_run_params PROFILE gcc )
        endif()
    endif()

    # other cases should be auto-detected by conan.cmake

    # Make sure to use conanfile.py to define dependencies, to stay consistent
    if ( EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/conanfile.py )
        set( CONANFILE conanfile.py )
    elseif( EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/conanfile.txt )
        set( CONANFILE conanfile.txt )
    endif()
    if ( NOT CONANFILE )
        message( FATAL_ERROR "Cannot find neither conanfile.py nor conanfile.txt in current source directory" )
    endif()
    mb_conan_cmake_run( CONANFILE ${CONANFILE} ${conan_cmake_run_params} BUILD missing )

    if ( CONAN_CMAKE_MULTI )
        # workaround for https://github.com/conan-io/conan/issues/1498
        # in our case, it's irrelevant which version is added - we need access to cmake files
        set(CMAKE_PREFIX_PATH ${CONAN_CMAKE_MODULE_PATH_RELEASE} ${CMAKE_PREFIX_PATH})
        set(CMAKE_MODULE_PATH ${CONAN_CMAKE_MODULE_PATH_RELEASE} ${CMAKE_MODULE_PATH})
    endif()
endif()

# if this include fails, then you have forgot to add
# build_requires = "CMakeBuild/[>=1.1.2,<2.0.0]@microblink/master"
# to your conanfile.py
include( common_settings )