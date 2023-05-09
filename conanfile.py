from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMake, CMakeDeps, CMakeToolchain
from conan.tools.files import copy, join


class CMakeLegacy:
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


class MicroblinkConanFile:
    options = {
        'log_level': ['Verbose', 'Debug', 'Info', 'WarningsAndErrors'],
        'enable_timer': [True, False],
    }
    default_options = {
        'log_level': 'WarningsAndErrors',
        'enable_timer': False,
    }
    settings = "os", "compiler", "build_type", "arch"

    def layout(self):
        cmake_layout(self)

    def compatibility(self):
        # Microblink's conan packages for Apple have universal binaries, so Mac and iOS simulator ship with both
        # support for Apple Silicon and Intel
        if self.settings.os == 'Macos' or (self.settings.os == 'iOS' and self.settings.os.sdk == 'iphonesimulator'):
            return [{"settings": [("arch", a)]} for a in ("armv8", "x86_64")]

    def mb_generate_with_cmake_args(self, *, cmake_args: dict = []):
        tc = CMakeToolchain(self)
        tc.variables.update(cmake_args)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def generate(self):
        self.mb_generate_with_cmake_args()

    # TODO: move this to log-and-timer package
    def mb_add_base_args(self, args):
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

    def mb_build_with_args(self, args, target=None):
        cmake = CMake(self)
        args.append(f'-DMB_CONAN_PACKAGE_NAME={self.name}')
        if self.settings.build_type == 'DevRelease':
            args.extend(['-DCMAKE_BUILD_TYPE=Release', '-DMB_DEV_RELEASE=ON'])

        self.mb_add_base_args(args)
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
                cmake.build(target=target)
        else:
            cmake.build(target=target)

    def mb_cmake_install(self):
        cmake = CMake(self)
        if self.settings.os == 'iOS':
            cmake.install(args=['--', '-sdk', self.settings.os.sdk, 'ONLY_ACTIVE_ARCH=NO'])
        elif self.settings.os == 'Macos' and self.settings.os.subsystem == 'catalyst':
            # CMake currently does not support invoking Mac Catalyst builds
            self.run(
                "xcodebuild build -configuration Release -scheme install " +
                "-destination 'platform=macOS,variant=Mac Catalyst' ONLY_ACTIVE_ARCH=NO"
            )
        else:
            cmake.install()

    def build(self):
        self.mb_build_with_args([])

    def mb_package_all_headers(self):
        copy(
            self,
            pattern="*.h*",
            src=join(self.source_folder, self.name, "Source"),
            dst=join(self.package_folder, "include"),
            keep_path=True
        )

    def mb_package_public_headers(self):
        copy(
            self,
            pattern="*.h*",
            src=join(self.source_folder, self.name, "Include"),
            dst=join(self.package_folder, "include"),
            keep_path=True
        )

    def mb_package_custom_libraries(self, libs, subfolders=['']):
        for lib in libs:
            if self.settings.os == 'Windows':
                copy(
                    self,
                    pattern=f"{lib}.lib",
                    src=join(self.build_folder, "lib"),
                    dst=join(self.package_folder, 'lib'),
                    keep_path=False
                )
                copy(
                    self,
                    pattern=f"*{lib}.pdb",
                    src=join(self.build_folder, "lib"),
                    dst=join(self.package_folder, "lib"),
                    keep_path=False
                )
            else:
                copy(
                    self,
                    pattern=f"{lib}.a",
                    src=join(self.build_folder, 'lib'),
                    dst=join(self.package_folder, "lib"),
                    keep_path=False
                )

            # TODO: see what happens with xcode builds

            # if self.settings.os == 'iOS':
            #     for subfolder in subfolders:
            #         if subfolder != '':
            #             prefix = f'{subfolder}/'
            #         else:
            #             prefix = ''
            #         copy(self, pattern=f"{prefix}Release-{self.settings.os.sdk}/{lib}.a", dst="lib", keep_path=False)
            #
            #         if self.settings.os.sdk != None:  # noqa: E711
            #             if self.settings.os.sdk == 'device':
            #                 self.copy(f"{prefix}Release-iphoneos/{lib}.a", dst="lib", keep_path=False)
            #             elif self.settings.os.sdk == 'simulator':
            #                 self.copy(f"{prefix}Release-iphonesimulator/{lib}.a", dst="lib", keep_path=False)
            #             elif self.settings.os.sdk == 'maccatalyst':
            #                 self.copy(f"{prefix}Release-maccatalyst/{lib}.a", dst="lib", keep_path=False)

    def mb_package_all_libraries(self, subfolders=['']):
        self.mb_package_custom_libraries(['*'], subfolders)

    def package(self):
        self.mb_package_public_headers()
        self.mb_package_all_libraries()

    def package_info(self):
        # TODO: move this to CMakeBuild package
        if self.settings.build_type == 'Debug' \
                and not conans.tools.cross_building(self.settings) and \
                self.settings.compiler in ['clang', 'apple-clang'] and \
                self.settings.os != 'Windows':
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
        super().configure()
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
        self.mb_build_with_args(self.common_recognizer_build_args())

    def package_id(self):
        self.common_settings_for_package_id()

    def package(self):
        self.mb_package_public_headers()
        self.mb_package_all_libraries()
        self.copy('features_*.cmake')
        self.copy('Dictionary/Dictionaries/*.zzip', dst='res')


class MicroblinkConanFilePackage(ConanFile):
    name = "conanfile-utils"
    version = "0.1.0"

# pylint: skip-file
