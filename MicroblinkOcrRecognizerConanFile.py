from conans import python_requires

base = python_requires('MicroblinkRecognizerConanFile/1.0.3@microblink/stable')

class MicroblinkRecognizerConanFile(base.MicroblinkRecognizerConanFile):

    def configure(self):
        self.options['Recognizer'].result_jsonization = self.options.result_jsonization
        self.options['Recognizer'].binary_serialization = self.options.binary_serialization
        self.options['BlinkInputRecognizer'].result_jsonization = self.options.result_jsonization
        self.options['BlinkInputRecognizer'].binary_serialization = self.options.binary_serialization