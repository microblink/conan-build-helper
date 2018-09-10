from conans import python_requires

base = python_requires('MicroblinkConanFile/1.0.2@microblink/stable')

class MicroblinkRecognizerConanFile(base.MicroblinkConanFile):
    options = dict(base.MicroblinkConanFile.options, **{
        'result_jsonization': ['Off', 'Serialization', 'SerializationAndTesting'],
        'binary_serialization': [True, False],
    })
    default_options = ('result_jsonization=Off',) + base.MicroblinkConanFile.default_options


    def config_options(self):
        if self.settings.os == 'Android':
            self.options.binary_serialization = True
        else:
            self.options.binary_serialization = False


    def configure(self):
        self.options['Recognizer'].result_jsonization = self.options.result_jsonization
        self.options['Recognizer'].binary_serialization = self.options.binary_serialization


    def build(self):
        self.build_with_args(self.common_recognizer_build_args())