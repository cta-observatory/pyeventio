def assert_exact_version(self, supported_version):
    if self.header.version != supported_version:
        raise NotImplementedError(
            (
                'Unsupported version of {name}: '
                'only supports version {supported_version}'
                'got {given_version}'
            ).format(
                name=self.__class__.__name__,
                supported_version=supported_version,
                given_version=self.header.version,
            )
        )


def assert_version_in(self, supported_versions):
    if self.header.version not in supported_versions:
        raise NotImplementedError(
            (
                'Unsupported version of {name}: '
                'supported versions are: {supported_versions}, '
                'got: {given_version} '
            ).format(
                name=self.__class__.__name__,
                supported_versions=supported_versions,
                given_version=self.header.version,
            )
        )


def assert_max_version(self, last_supported):
    if self.header.version > last_supported:
        raise NotImplementedError(
            (
                'Unsupported version of {name}: '
                'only versions up to {last_supported} supported, '
                'got: {given_version} '
            ).format(
                name=self.__class__.__name__,
                last_supported=last_supported,
                given_version=self.header.version,
            )
        )
