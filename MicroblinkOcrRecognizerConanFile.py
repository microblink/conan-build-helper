from conans import python_requires

base = python_requires('MicroblinkRecognizerConanFile/1.0.4@microblink/stable')

class MicroblinkOcrRecognizerConanFile(base.MicroblinkRecognizerConanFile):

    def configure(self):
        self.options['Recognizer'].result_jsonization = self.options.result_jsonization
        self.options['Recognizer'].binary_serialization = self.options.binary_serialization
        self.options['Recognizer'].enable_testing = self.options.enable_testing
        self.options['BlinkInputRecognizer'].result_jsonization = self.options.result_jsonization
        self.options['BlinkInputRecognizer'].binary_serialization = self.options.binary_serialization
        self.options['BlinkInputRecognizer'].enable_testing = self.options.enable_testing