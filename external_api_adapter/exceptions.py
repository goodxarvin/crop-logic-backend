class ExternalAPIAdapterError(Exception):
    pass


class ServiceNotFound(ExternalAPIAdapterError):
    pass


class MockDirectoryNotFound(ExternalAPIAdapterError):
    pass


class MockFileNotFound(ExternalAPIAdapterError):
    pass


class ExternalAPIRequestError(ExternalAPIAdapterError):
    pass
