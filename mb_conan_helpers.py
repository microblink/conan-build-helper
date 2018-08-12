from conans import ConanFile, tools


class MicroblinkConanFile(ConanFile):
    def build(self):
        from microblink import CMake
        cmake = CMake(self, build_type = 'Release') # always build release, whether full release or dev-release (in debug mode)
        args = []
        if self.settings.build_type == 'Debug':
            args = ['-DCMAKE_BUILD_TYPE=Release', '-DMB_DEV_RELEASE=ON']
            # runtime checks on Android require rooted device, and on iOS special
            # checkbox enabled that we currently do not support setting via CMake
            if self.settings.os != 'iOS' and self.settings.os != 'Android':
                args.append('-DMB_ENABLE_RUNTIME_CHECKS=ON')
        cmake.configure(args = args)
        cmake.build()


    def package(self):
        self.copy("*.hpp", dst="include", src="Source")

        if self.settings.os == 'Windows':
            self.copy("*.lib", dst="lib", keep_path=False)
            self.copy("*.pdb", dst="lib", keep_path=False)

        if self.settings.os == 'iOS':
            # copy fat libraries
            self.copy("*/Release/*.a", dst="lib", keep_path=False)
        else:
            self.copy("*.a", dst="lib", keep_path=False)


    def build_id(self):
        if self.settings.os == 'iOS':
            self.info_build.settings.arch = 'All'
            self.info_build.settings.os.version = '8.0'
        if self.settings.os == 'Android':
            self.info_build.settings.os.api_level = 16


    def package_id(self):
        # Apple has fat libraries, so no need for having separate packages
        if self.settings.os == 'iOS':
            self.info.settings.arch = "All"

        # Sett all 'requires' dependencies to 'full package mode', i.e. whenever
        # anything in those dependencies change, this package needs to be rebuilt
        for r in self.requires:
            self.info.requires[r].full_package_mode()


    def package_info(self):
        if self.settings.build_type == 'Debug' and not tools.cross_building(self.settings) and (self.settings.compiler == 'clang' or self.settings.compiler == 'apple-clang'):
            # runtime checks are enabled, so we need to add ASAN/UBSAN linker flags
            runtime_check_flags = [ '-fsanitize=undefined', '-fsanitize=address']
            if self.settings.compiler == 'clang':
                runtime_check_flags.append('-fsanitize=integer')
            self.cpp_info.sharedlinkflags.extend(runtime_check_flags)
            self.cpp_info.exelinkflags.extend(runtime_check_flags)
