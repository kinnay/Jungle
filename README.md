
This projects implements parsers for various file formats can be found in Nintendo games. It has been written to support [research](https://github.com/kinnay/Nintendo-File-Formats), and it is also used in a [viewer tool](https://github.com/kinnay/panorama).

## Installation
This package can be installed with `pip3 install jungle-package`.

Python 3.13 or later is required.

**Note:** this package does not have a stable interface. It is recommended to pin its version.

## Testing
Every parser that is implemented in this package must be sound and complete. This means that, given an arbitrary file from a Nintendo game, decoding and reencoding that file must always produce the original file again.

This can be tricky to implement for some file formats (especially if Nintendo's tooling is inconsistent or has quirks), but it is a hard requirement for this repository. A [`test.py`](https://github.com/kinnay/Jungle/blob/main/test.py) script has been written to verify this. If you come across a file in a game that should be supported by this repository, but fails the test, feel free to reach out on [discord](https://discord.gg/x8np6Hhxwk) or [contribute research](#contributing).

## Supported Formats
Many different file formats are supported. Check out the [jungle](https://github.com/kinnay/Jungle/blob/main/jungle) folder to see which file formats are currently supported.

## Contributing
The best way to contribute is to reverse engineer file formats and provide documentation for them. New documentation can be submitted as a pull request to the [Nintendo file formats](https://github.com/kinnay/Nintendo-File-Formats) wiki. Bug fixes and corrections to existing documentation are also more than welcome.

If you would like to chat about Nintendo's file formats in general, feel free to join the [Discord server](https://discord.gg/x8np6Hhxwk).
