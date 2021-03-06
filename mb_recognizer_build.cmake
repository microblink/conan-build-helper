set( Recognizer_RESULT_JSONIZATION "SerializationAndTesting" CACHE STRING "JSON interop support level for recognizer result structures" )
set_property( CACHE Recognizer_RESULT_JSONIZATION PROPERTY STRINGS "Off" "Serialization" "SerializationAndTesting" )

option( Recognizer_BINARY_SERIALIZATION "Enable binary serialization of results and settings" ON )

option( Recognizer_ENABLE_IMSHOW "Enable imshow" OFF )

if( NOT CONAN_EXPORTED )
    list( APPEND MB_CONAN_SETUP_PARAMS OPTIONS "result_jsonization=${Recognizer_RESULT_JSONIZATION}" "Protection:all_keys=True" )
    if ( Recognizer_BINARY_SERIALIZATION )
        list( APPEND MB_CONAN_SETUP_PARAMS OPTIONS "binary_serialization=True" )
    endif()

    if ( Recognizer_ENABLE_IMSHOW )
        list( APPEND MB_CONAN_SETUP_PARAMS OPTIONS "MVToolset:enable_imshow=True" )
    endif()
endif()

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

remote_include( "mb_conan_build.cmake" "http://raw.githubusercontent.com/microblink/conan-build-helper/master/mb_conan_build.cmake" "http://files.microblink.com/mb_conan_build.cmake" )

macro( print_recognizer_options )
    include(print_info_main)
    print_info_main()

    print_title( "Recognizer options" )
    print_cache_var( Recognizer_RESULT_JSONIZATION   )
    print_cache_var( Recognizer_BINARY_SERIALIZATION )
    print_cache_var( Recognizer_ENABLE_IMSHOW )
endmacro()
