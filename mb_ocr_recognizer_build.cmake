set( RECOGNIZER_DEPENDENCY "BlinkInputRecognizer" )

if( NOT EXISTS "${CMAKE_BINARY_DIR}/mb_recognizer_build.cmake" )
    message( STATUS "Downloading mb_recognizer_build.cmake from https://github.com/microblink/conan-build-helper" )
    file( DOWNLOAD "https://raw.githubusercontent.com/microblink/conan-build-helper/master/mb_recognizer_build.cmake" "${CMAKE_BINARY_DIR}/mb_recognizer_build.cmake" )
endif()

include( ${CMAKE_BINARY_DIR}/mb_recognizer_build.cmake )