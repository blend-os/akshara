# akshara

A simple system builder and immutability layer.

## Development

To test a modified copy of `akshara`, run the following on a working blendOS install:

```sh
sudo umount -l /usr && sudo mv ./akshara /usr/bin/akshara && sudo chmod +x /usr/bin/akshara
```

Replace `./akshara` with wherever your modified copy of `akshara` is.

⚠ **ANY CHANGES TO `/usr/bin/akshara` WILL BE REVERTED AFTER EVERY UPDATE!** ⚠
