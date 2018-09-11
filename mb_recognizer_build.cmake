set( Recognizer_RESULT_JSONIZATION "SerializationAndTesting" CACHE STRING "JSON interop support level for recognizer result structures" )
set_property( CACHE Recognizer_RESULT_JSONIZATION PROPERTY STRINGS "Off" "Serialization" "SerializationAndTesting" )

option( Recognizer_BINARY_SERIALIZATION "Enable binary serialization of results and settings" ON )

option( Recognizer_ENABLE_TESTING "Enable RecognizerTests" ON )

if( NOT CONAN_EXPORTED )
    list( APPEND MB_CONAN_SETUP_PARAMS OPTIONS "result_jsonization=${Recognizer_RESULT_JSONIZATION}" "Protection:all_keys=True" "MVToolset:enable_image_io=True" )
    if ( Recognizer_BINARY_SERIALIZATION )
        list( APPEND MB_CONAN_SETUP_PARAMS OPTIONS "binary_serialization=True" )
    endif()
    if ( Recognizer_ENABLE_TESTING )
        list( APPEND MB_CONAN_SETUP_PARAMS OPTIONS "Recognizer:enable_testing=True" )
    endif()
endif()

if( NOT EXISTS "${CMAKE_BINARY_DIR}/mb_conan_build.cmake" )
    message( STATUS "Downloading mb_conan_build.cmake from https://github.com/microblink/conan-build-helper" )
    file( DOWNLOAD "https://raw.githubusercontent.com/microblink/conan-build-helper/master/mb_conan_build.cmake" "${CMAKE_BINARY_DIR}/mb_conan_build.cmake" )
endif()

include( ${CMAKE_BINARY_DIR}/mb_conan_build.cmake )

macro( print_recognizer_options )
    print_title( "Recognizer options" )
    print_cache_var( Recognizer_RESULT_JSONIZATION   )
    print_cache_var( Recognizer_BINARY_SERIALIZATION )
    print_cache_var( Recognizer_ENABLE_TESTING )
endmacro()