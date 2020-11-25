import conans
import os


class CMake(conans.CMake):
    def configure(self, args=None, defs=None, source_folder=None, build_folder=None,
                  cache_build_folder=None, pkg_config_paths=None):
        env_prefix = "CONAN_CMAKE_CUSTOM_"
        cmake_params = [
            "-D%s=%s" % (key.replace(env_prefix, ''), value)
            for key, value in os.environ.items() if key.startswith(env_prefix)
        ]
        if args is not None:
            args.extend(cmake_params)
        else:
            args = cmake_params
        super().configure(
            args=args, defs=defs, source_folder=source_folder, build_folder=build_folder,
            cache_build_folder=cache_build_folder, pkg_config_paths=pkg_config_paths
        )


class MicroblinkConanFile(object):
    options = {
        'log_level': ['Verbose', 'Debug', 'Info', 'WarningsAndErrors'],
        'enable_timer': [True, False],
        'enable_testing': [True, False]
    }
    default_options = {
        'log_level': 'WarningsAndErrors',
        'enable_timer': False,
        'enable_testing': False
    }
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    no_copy_source = True

    def add_base_args(self, args):
        if 'log_level' in self.options:
            if self.options.log_level == 'Verbose':
                args.append('-DMB_GLOBAL_LOG_LEVEL=LOG_VERBOSE')
            elif self.options.log_level == 'Debug':
                args.append('-DMB_GLOBAL_LOG_LEVEL=LOG_DEBUG')
            elif self.options.log_level == 'Info':
                args.append('-DMB_GLOBAL_LOG_LEVEL=LOG_INFO')
            elif self.options.log_level == 'WarningsAndErrors':
                args.append('-DMB_GLOBAL_LOG_LEVEL=LOG_WARNINGS_AND_ERRORS')

        if 'enable_timer' in self.options:
            if self.options.enable_timer:
                args.append('-DMB_GLOBAL_ENABLE_TIMER=ON')

        if 'enable_testing' in self.options:
            args.append(f'-DMB_ENABLE_TESTING={self.options.enable_testing}')

    def build_with_args(self, args):
        # always build release, whether full release or dev-release (in debug mode)
        cmake = CMake(self, build_type='Release')
        args.append(f'-DMB_CONAN_PACKAGE_NAME={self.name}')
        if self.settings.build_type == 'Debug':
            args.extend(['-DCMAKE_BUILD_TYPE=Release', '-DMB_DEV_RELEASE=ON'])
            # runtime checks on Android require rooted device, and on iOS special
            # checkbox enabled that we currently do not support setting via CMake
            if self.settings.os != 'iOS' and self.settings.os != 'Android':
                args.append('-DMB_ENABLE_RUNTIME_CHECKS=ON')

        self.add_base_args(args)
        # this makes packages forward compatible with future compiler updates
        args.append('-DMB_TREAT_WARNINGS_AS_ERRORS=OFF')
        cmake.configure(args=args)
        if self.settings.os == 'iOS':
            if self.settings.os.sdk != None:  # noqa: E711
                if self.settings.os.sdk == 'device':
                    cmake.build(args=['--', '-sdk', 'iphoneos', 'ONLY_ACTIVE_ARCH=NO'])
                elif self.settings.os.sdk == 'simulator':
                    cmake.build(args=['--', '-sdk', 'iphonesimulator', 'ONLY_ACTIVE_ARCH=NO'])
                elif self.settings.os.sdk == 'maccatalyst':
                    # CMake currently does not support invoking Mac Catalyst builds
                    self.run(
                        "xcodebuild build -configuration Release -scheme ALL_BUILD " +
                        "-destination 'platform=macOS,variant=Mac Catalyst' ONLY_ACTIVE_ARCH=NO"
                    )
            else:
                # backward compatibility with old iOS toolchain and CMakeBuild < 12.0.0
                cmake.build()
        else:
            cmake.build()

    def build(self):
        self.build_with_args([])

    def package_all_headers(self):
        self.copy("*.h*", dst="include", src=f"{self.name}/Source")

    def package_public_headers(self):
        self.copy("*.h*", dst="include", src=f"{self.name}/Include")

    def package_all_libraries(self):
        if self.settings.os == 'Windows':
            self.copy("*.lib", dst="lib", keep_path=False)
            self.copy("*.pdb", dst="lib", keep_path=False)

        if self.settings.os == 'iOS':
            if self.settings.os.sdk != None:  # noqa: E711
                if self.settings.os.sdk == 'device':
                    self.copy("Release-iphoneos/*.a", dst="lib", keep_path=False)
                elif self.settings.os.sdk == 'simulator':
                    self.copy("Release-iphonesimulator/*.a", dst="lib", keep_path=False)
                elif self.settings.os.sdk == 'maccatalyst':
                    self.copy("Release-maccatalyst/*.a", dst="lib", keep_path=False)
                # Cases when add_subdirectory is used (GTest, cpuinfo)
                self.copy("*.a", src='lib', dst="lib", keep_path=False)
            else:
                # First copy device-only libraries (in case fat won't exists (i.e. CMakeBuild >= 12.0.0 is used))
                self.copy("Release-iphoneos/*.a", dst="lib", keep_path=False)
                # copy fat libraries if they exist (and overwrite those copied in previous step)
                self.copy("*Release/*.a", dst="lib", keep_path=False)
        else:
            self.copy("*.a", src='lib', dst="lib", keep_path=False)

    def package(self):
        self.package_public_headers()
        self.package_all_libraries()

    def imports(self):
        self.copy("*.dll", "", "bin")
        self.copy("*.dylib", "", "lib")
        self.copy("*.zzip", src='res', dst='')
        self.copy("*.pod", src='res', dst='')
        self.copy("*.strop", src='res', dst='')
        self.copy("*.rtttl", src='res', dst='')

    def ignore_testing_for_package_id(self):
        del self.info.options.enable_testing

    def common_settings_for_package_id(self):
        # Conan uses semver_mode by default for all dependencies. However,
        # we want some specific dependencies to be used in full_package mode,
        # most notably header only libraries.
        # Dependency user can always override this default behaviour.
        full_package_mode_deps = {
            'Boost',
            'Eigen',
            'range-v3',
            'RapidJSON',
            'UTFCpp',
            'Variant'
        }
        for r in self.requires:
            if r in full_package_mode_deps:
                self.info.requires[r].full_package_mode()

    def package_id(self):
        self.ignore_testing_for_package_id()
        self.common_settings_for_package_id()

    def package_info(self):
        if self.settings.build_type == 'Debug' \
           and not conans.tools.cross_building(self.settings) and \
           self.settings.compiler in ['clang', 'apple-clang']:
            # runtime checks are enabled, so we need to add ASAN/UBSAN linker flags
            runtime_check_flags = ['-fsanitize=undefined', '-fsanitize=address']
            if self.settings.compiler == 'clang':
                runtime_check_flags.append('-fsanitize=integer')
            self.cpp_info.sharedlinkflags.extend(runtime_check_flags)
            self.cpp_info.exelinkflags.extend(runtime_check_flags)


class MicroblinkRecognizerConanFile(MicroblinkConanFile):
    options = {
        'result_jsonization': ['Off', 'Serialization', 'SerializationAndTesting'],
        'binary_serialization': [True, False]
    }
    default_options = {
        'result_jsonization': 'Off'
    }

    def init(self):
        base = self.python_requires['MicroblinkConanFile'].module.MicroblinkConanFile
        self.options.update(base.options)
        self.default_options.update(base.default_options)

    def config_options(self):
        if self.options.binary_serialization == None:  # noqa: E711
            if self.settings.os == 'Android':
                self.options.binary_serialization = True
            else:
                self.options.binary_serialization = False

    def configure(self):
        self.options['*'].result_jsonization = self.options.result_jsonization
        self.options['*'].binary_serialization = self.options.binary_serialization
        self.options['*'].enable_testing = self.options.enable_testing

    def common_recognizer_build_args(self):
        cmake_args = [
            f'-DRecognizer_RESULT_JSONIZATION={self.options.result_jsonization}',
            f'-DRecognizer_BINARY_SERIALIZATION={self.options.binary_serialization}',
            f'-DMB_ENABLE_TESTING={self.options.enable_testing}'
        ]
        return cmake_args

    def build(self):
        self.build_with_args(self.common_recognizer_build_args())

    def package_id(self):
        self.common_settings_for_package_id()

    def package(self):
        self.package_public_headers()
        self.package_all_libraries()
        self.copy('features_*.cmake')
        self.copy('Dictionary/Dictionaries/*.zzip', dst='res')


class MicroblinkConanFilePackage(conans.ConanFile):
    name = "MicroblinkConanFile"
    version = "7.0.0"
