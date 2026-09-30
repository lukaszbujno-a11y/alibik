# About the Rooster and the Hen (O kohoutkovi a slepičce)
The final directory contains the finished book.

The podklady directory contains the source data.

## Building the sample book (test)
Rebuilding the sample book from the source data is a quick end-to-end check of `bnl_creator.pl`
and of `podklady/bnl.yaml`. The result must be byte-identical to `final/slepicka.bnl`.

### Requirements
- Perl 5 with the `YAML` module (check with `perl -MYAML -e1`, install with `cpan YAML` if it is missing)
- `unzip`

### Steps
`bnl_creator.pl` looks for the mp3 files in the current directory and also writes `generate_oids.yaml` there,
so run it in a separate working directory, not in the repository. Run from the repository root:

```sh
REPO="$PWD"
mkdir -p /tmp/bnl_test
unzip -o -q test/podklady/mp3.zip -d /tmp/bnl_test
cp test/podklady/bnl.yaml /tmp/bnl_test/
cd /tmp/bnl_test
perl "$REPO/tools/creator/bnl_creator.pl" -input bnl.yaml -output slepicka.bnl
```

The output should end with:
```
Created slepicka.bnl, 5819128 bytes long.
Done.
```

### Verifying the result
```sh
cmp slepicka.bnl "$REPO/test/final/slepicka.bnl" && echo OK
```
`OK` means the built book is identical to the reference one.

### Troubleshooting
- `Invalid oid format ''` - the YAML uses old quiz key names (`q1_oid`, `q1_unk`, `q1_good_reply_oids`).
  For quiz type 0 the keys must be `q0_oid`, `q0_unk` and `q0_good_reply_oids`.
- `Can't locate YAML.pm` - the `YAML` Perl module is not installed.

### Cleanup
```sh
cd "$REPO"
rm -rf /tmp/bnl_test
```
