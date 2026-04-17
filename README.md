
This projects implements parsers for various file formats can be found in Nintendo games. It has been written to support [research](https://github.com/kinnay/Nintendo-File-Formats), and it is also used in a [viewer tool](https://github.com/kinnay/panorama).

## Installation
The package is currently not available on pip, but it can be installed as follows:

```bash
git clone https://github.com/kinnay/jungle.git jungle
cd jungle
pip3 install .
```

## Testing
Every parser that is implemented in this package must be sound and complete. This means that, given an arbitrary file from a Nintendo game, decoding and reencoding that file must always produce the original file again.

This can be tricky to implement for some file formats (especially if Nintendo's tooling is inconsistent or has quirks), but it is a hard requirement for this repository. A [`test.py`](https://github.com/kinnay/Jungle/blob/main/test.py) script has been written to verify this. If you come across a file in a game that should be supported by this repository, but fails the test, feel free to reach out on [discord](https://discord.gg/x8np6Hhxwk) or [contribute research](#contributing).

## Supported Formats
The following file formats are currently supported by this library:

| Library | Format | Extensions | Description |
| --- | --- | --- | --- |
| Multiple | [BYAML](https://nintendo-formats.com/libs/common/byaml.html) | `.byml` / `.byaml` / `.bgyml` | Binary YAML |
| AAL | [BAATN](https://nintendo-formats.com/libs/aal/baatn.html) | `.baatn` | Audio attenuators |
| AAL | [BAMETA](https://nintendo-formats.com/libs/aal/bameta.html) | `.bameta` | Audio metadata |
| AAL | [BARS](https://nintendo-formats.com/libs/aal/bars.html) | `.bars` | Audio resources |
| AAL | [BARSLIST](https://nintendo-formats.com/libs/aal/barslist.html) | `.barslist` | Audio resource lists |
| AGL | [PMAA](https://nintendo-formats.com/libs/agl/pmaa.html) | `.bagl*` | Graphics parameters |
| CAS | [BAEV](https://nintendo-formats.com/libs/cas/baev.html) | `.baev` | Animation event archive |
| GFD | [Gfx2](https://nintendo-formats.com/libs/gfd/gfx2.html) | `.gtx` / `.gsh` | Textures and shaders |
| LMS | [MSBP](https://nintendo-formats.com/libs/lms/msbp.html) | `.msbp` | Message projects |
| NW4F | [BFWAV](https://nintendo-formats.com/libs/nw/bfwav.html) | `.bfwav` | Wave files |
| SEAD | [SARC](https://nintendo-formats.com/libs/sead/sarc.html) | `.sarc` | Archives |
| SEAD | [SZS](https://nintendo-formats.com/libs/sead/yaz0.html) | `.szs` | Yaz0 compression |
| XLINK | [SLINK](https://nintendo-formats.com/libs/xlink/slink.html) | `.slink` | Sound links |

For some file formats, only specific versions are currently supported.

## Contributing
The best way to contribute is to reverse engineer file formats and provide documentation for them. New documentation can be submitted as a pull request to the [Nintendo file formats](https://github.com/kinnay/Nintendo-File-Formats) wiki. Bug fixes and corrections to existing documentation are also more than welcome.

If you would like to chat about Nintendo's file formats in general, feel free to join the [Discord server](https://discord.gg/x8np6Hhxwk).
