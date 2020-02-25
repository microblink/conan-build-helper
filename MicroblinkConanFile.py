from conans import ConanFile, tools


class MicroblinkConanFile(ConanFile):
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
        from microblink import CMake
        # always build release, whether full release or dev-release (in debug mode)
        cmake = CMake(self, build_type='Release')
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
        cmake.build()


    def build(self):
        self.build_with_args([])


    def package_all_headers(self):
        self.copy("*.h*", dst="include", src=f"{self.name}/Source")


    def package_all_libraries(self):
        if self.settings.os == 'Windows':
            self.copy("*.lib", dst="lib", keep_path=False)
            self.copy("*.pdb", dst="lib", keep_path=False)

        if self.settings.os == 'iOS':
            # copy fat libraries
            self.copy("*Release/*.a", dst="lib", keep_path=False)
        else:
            self.copy("*.a", dst="lib", keep_path=False)


    def package(self):
        self.package_all_headers()
        self.package_all_libraries()


    def build_id(self):
        if self.info_build.settings.os is not None:
            if self.settings.os == 'iOS':
                self.info_build.settings.arch = 'ios_fat'
                self.info_build.settings.os.version = '8.0'
            if self.settings.os == 'Android':
                self.info_build.settings.os.api_level = 16


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
        # Apple has fat libraries, so no need for having separate packages
        if self.settings.os == 'iOS':
            self.info.settings.arch = "ios_fat"

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
        if self.settings.build_type == 'Debug' and not tools.cross_building(self.settings) and \
                (self.settings.compiler == 'clang' or self.settings.compiler == 'apple-clang'):
            # runtime checks are enabled, so we need to add ASAN/UBSAN linker flags
            runtime_check_flags = ['-fsanitize=undefined', '-fsanitize=address']
            if self.settings.compiler == 'clang':
                runtime_check_flags.append('-fsanitize=integer')
            self.cpp_info.sharedlinkflags.extend(runtime_check_flags)
            self.cpp_info.exelinkflags.extend(runtime_check_flags)
