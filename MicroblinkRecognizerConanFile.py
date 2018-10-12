from conans import python_requires

base = python_requires('MicroblinkConanFile/3.0.1@microblink/stable')

class MicroblinkRecognizerConanFile(base.MicroblinkConanFile):
    options = dict(base.MicroblinkConanFile.options, **{
        'result_jsonization': ['Off', 'Serialization', 'SerializationAndTesting'],
        'binary_serialization': [True, False]
    })
    default_options = dict(base.MicroblinkConanFile.default_options, **{
        'result_jsonization' : 'Off'
    })


    def config_options(self):
        if self.options.binary_serialization == None:
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
        self.package_all_headers()
        self.package_all_libraries()
        self.copy('features_*.cmake')
        self.copy('Dictionary/Dictionaries/*.zzip', dst='res')