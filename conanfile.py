from conan import ConanFile
from conan.tools.cmake import cmake_layout, CMake, CMakeDeps, CMakeToolchain
from conan.tools.files import copy, load
from os.path import join


class MicroblinkConanFile:
    # options = {
    #     'log_level': ['Verbose', 'Debug', 'Info', 'WarningsAndErrors'],
    #     'enable_timer': [True, False],
    # }
    # default_options = {
    #     'log_level': 'WarningsAndErrors',
    #     'enable_timer': False,
    # }
    settings = "os", "compiler", "build_type", "arch"
    no_copy_source = True
    export_sources = '*', '!test-data/*', '!.git/*'
    package_type = 'static-library'

    # -----------------------------------------------------------------------------
    # Now follow the mb-specific methods
    # -----------------------------------------------------------------------------

    def mb_generate_with_cmake_args(self, cmake_args: dict = []):
        custom_cmake_options_key = 'user.microblink.cmaketoolchain:cache_variables'

        cmake_build = self.dependencies['cmake-build']

        tc = CMakeToolchain(self)

        if cmake_build is not None:
            custom_cmake_options = cmake_build.conf_info.get(custom_cmake_options_key)
            tc.variables.update(custom_cmake_options)

            tc.variables.update(
                {
                    'MB_CONAN_PACKAGE_NAME': self.name,
                    'MB_TREAT_WARNINGS_AS_ERRORS': 'OFF',
                }
            )
            if self.settings.build_type == 'DevRelease':
                tc.variables.update(
                    {
                        'CMAKE_BUILD_TYPE': 'Release',
                        'MB_DEV_RELEASE': 'ON',
                    }
                )

        tc.variables.update(cmake_args)
        tc.generate()

        deps = CMakeDeps(self)
        if self.settings.build_type == 'DevRelease':
            deps.configuration = 'Release'
        deps.generate()

    # TODO: move this to log-and-timer package
    # def mb_add_base_args(self, args):
    #     if 'log_level' in self.options:
    #         if self.options.log_level == 'Verbose':
    #             args.append('-DMB_GLOBAL_LOG_LEVEL=LOG_VERBOSE')
    #         elif self.options.log_level == 'Debug':
    #             args.append('-DMB_GLOBAL_LOG_LEVEL=LOG_DEBUG')
    #         elif self.options.log_level == 'Info':
    #             args.append('-DMB_GLOBAL_LOG_LEVEL=LOG_INFO')
    #         elif self.options.log_level == 'WarningsAndErrors':
    #             args.append('-DMB_GLOBAL_LOG_LEVEL=LOG_WARNINGS_AND_ERRORS')
    #
    #     if 'enable_timer' in self.options:
    #         if self.options.enable_timer:
    #             args.append('-DMB_GLOBAL_ENABLE_TIMER=ON')
    #
    #     if 'enable_testing' in self.options:
    #         args.append(f'-DMB_ENABLE_TESTING={self.options.enable_testing}')
    #
    def mb_build_target(self, target=None):
        cmake = CMake(self)
        cmake.configure()

        if self.settings.os == 'iOS':
            cmake.build(target=target, build_tool_args=['-sdk', self.settings.os.sdk, 'ONLY_ACTIVE_ARCH=NO'])
        elif self.settings.os == 'Macos' and self.settings.os.subsystem == 'catalyst':
            # CMake currently does not support invoking Mac Catalyst builds
            if target is None:
                target = 'ALL_BUILD'
            self.run(
                f"xcodebuild build -configuration Release -scheme {target} " +
                "-destination 'platform=macOS,variant=Mac Catalyst' ONLY_ACTIVE_ARCH=NO"
            )
        else:
            cmake.build(target=target)

    def mb_cmake_install(self):
        cmake = CMake(self)
        if self.settings.os == 'iOS':
            # cmake.install in conan v2 does not support build_tool_args, like cmake.build
            self.run(
                "xcodebuild build -configuration Release -scheme install " +
                f"-sdk {self.settings.os.sdk} ONLY_ACTIVE_ARCH=NO"
            )
        elif self.settings.os == 'Macos' and self.settings.os.subsystem == 'catalyst':
            # CMake currently does not support invoking Mac Catalyst builds
            self.run(
                "xcodebuild build -configuration Release -scheme install " +
                "-destination 'platform=macOS,variant=Mac Catalyst' ONLY_ACTIVE_ARCH=NO"
            )
        else:
            cmake.install()

    def mb_testing_enabled(self):
        # NOTE: skip_test off by default, can be enabled with '-c tools.build:skip_test=True' when invoking conan
        skip_test = self.conf.get('tools.build:skip_test', default=False)
        return not skip_test

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

    def mb_define_apple_universal_binary(self):
        if self.info.settings.os == 'Macos' or \
                (self.info.settings.os == 'iOS' and self.info.settings.os.sdk == 'iphonesimulator'):
            cmake_generator = self.conf.get('tools.cmake.cmaketoolchain:generator', default='Xcode')
            if cmake_generator == 'Xcode':
                self.info.settings.arch = 'universal'

    # -----------------------------------------------------------------------------
    # Now follow the default implementations of conan methods (no mb_ prefix)
    # -----------------------------------------------------------------------------

    def set_version(self):
        """Automatically parse version from README.md"""

        if self.version is None:
            # load the version from README.md
            readme = load(self, join(self.recipe_folder, 'README.md'))
            assert readme is not None
            regex = r"^##\s+(\d+.\d+.\d)+\s+$"
            import re
            version_match = re.search(regex, readme, re.MULTILINE)
            assert version_match is not None
            self.version = version_match.group(1)

    def layout(self):
        cmake_layout(self)

    def generate(self):
        self.mb_generate_with_cmake_args()

    def build(self):
        self.mb_build_target()

    def package(self):
        self.mb_cmake_install()

    def package_id(self):
        self.mb_define_apple_universal_binary()


class MicroblinkRecognizerConanFile(MicroblinkConanFile):
    options = {
        'result_jsonization': ['Off', 'Serialization', 'SerializationAndTesting'],
        'binary_serialization': [True, False]
    }
    default_options = {
        'result_jsonization': 'Off'
    }

    def init(self):
        base = self.python_requires['conanfile-utils'].module.MicroblinkConanFile
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

    def mb_common_recognizer_generate_args(self):
        cmake_args = {
            'Recognizer_RESULT_JSONIZATION': self.options.result_jsonization,
            'Recognizer_BINARY_SERIALIZATION': self.options.binary_serialization,
        }
        return cmake_args

    def generate(self):
        self.mb_generate_with_cmake_args(self.mb_common_recognizer_generate_args())

    def package(self):
        self.mb_package_public_headers()
        self.mb_package_all_libraries()
        self.copy('features_*.cmake')
        self.copy('Dictionary/Dictionaries/*.zzip', dst='res')


class MicroblinkConanFilePackage(ConanFile):
    name = "conanfile-utils"
    version = "0.1.0"
    package_type = 'python-require'

# pylint: skip-file
