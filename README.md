dbp.noobdev.io Site Generator
-----------------------------

For testing, run the following command to generate a working tree:

```sh
./create_sample_tree.sh
```

This will create a dummy file tree in the `sample` folder. Then, to generate the HTML, run:

```sh
./generate.sh -s sample/DualBootPatcher -t sample/tree -d sample.json
```

The resulting HTML files will be in `sample/tree`.
