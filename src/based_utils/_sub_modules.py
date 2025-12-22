class SubpackageImportError(ImportError):
    def __init__(self, *, name: str) -> None:
        super().__init__(f"Install package as based-utils[{name}].")
