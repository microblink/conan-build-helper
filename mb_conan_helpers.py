from conans import ConanFile


class MicroblinkConanFile(ConanFile):
    def build(self):
        from microblink import CMake
        cmake = CMake(self, build_type = 'Release') # always build release, whether full release or dev-release (in debug mode)
        args = []
        if self.settings.build_type == 'Debug':
            args = ['-DCMAKE_BUILD_TYPE=Release', '-DMB_DEV_RELEASE=ON', '-DMB_ENABLE_RUNTIME_CHECKS=ON']
        cmake.configure(args = args)
        cmake.build()


    def package(self):
        self.copy("*.hpp", dst="include", src="Source")
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)
        self.copy("*.pdb", dst="lib", keep_path=False)


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

    def package_info(self):
        if self.settings.build_type == 'Debug' and (self.settings.compiler == 'clang' or self.settings.compiler == 'apple-clang'):
            # runtime checks are enabled, so we need to add ASAN/UBSAN linker flags
            runtime_check_flags = [ '-fsanitize=undefined', '-fsanitize=address']
            if self.settings.compiler == 'clang':
                runtime_check_flags.append('-fsanitize=integer')
            self.cpp_info.sharedlinkflags.extend(runtime_check_flags)
            self.cpp_info.exelinkflags.extend(runtime_check_flags)
